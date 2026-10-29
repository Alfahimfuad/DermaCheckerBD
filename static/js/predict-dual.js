/* predict-dual.js
 * -----------------------------------------------------------------------------
 * Drives the dual-prediction buttons (Predict Dermoscopic Image +
 * Predict Phone Image) on BOTH pages that share them:
 *
 *   - /predict/        (templates/predictor/upload.html)
 *   - /quality/        (templates/photo_guide/quality_check.html)
 *
 * Both pages render the same markup shape:
 *   #submitBtnDermo  / #submitBtnPhone              (upload page)
 *   #qualityRunDermo / #qualityRunPhone             (quality-check page)
 *   #phoneMetadataModal + #phoneMetadataForm        (both pages, identical)
 *   #predictionOverlay + #predictionStages          (shared, included via
 *                                                    predictor/_prediction_overlay.html)
 *
 * Behaviour
 * ---------
 *   - Dermoscopic button: native form submission to /predict/ (the existing
 *     HAM10000 endpoint). Shows the shared scanning overlay while the
 *     browser is waiting for the redirect to the result page.
 *   - Phone button: opens the metadata modal. On submit, decodes the
 *     currently-selected image to a Blob, builds FormData with metadata,
 *     and POSTs to /predict/phone-image/ via fetch. Same scanning overlay.
 *   - Duplicate submissions are blocked while a request is in flight.
 *   - The overlay is always stopped on success, failure, timeout, or
 *     cancellation — no fake timers claiming a prediction completed.
 * -----------------------------------------------------------------------------
 */
(function () {
  'use strict';

  function t(key, fallback) {
    if (window.DERMA && window.DERMA.t) {
      try { return window.DERMA.t(key, fallback); } catch (e) {}
    }
    return fallback;
  }

  function getOverlay() {
    return document.getElementById('predictionOverlay');
  }

  function getScanImage() {
    return document.getElementById('predictionScanImage');
  }

  function getStages() {
    return document.querySelectorAll('#predictionStages .prediction-stage');
  }

  function getImageSource() {
    // On the upload page the uploader exposes the currently-selected File.
    // On the quality-check page the data URL is in runButton.dataset.imageUrl.
    if (window.DERMA_QUALITY && window.DERMA_QUALITY.getImageDataUrl) {
      return { kind: 'dataUrl', value: window.DERMA_QUALITY.getImageDataUrl() };
    }
    if (window.DERMA_UPLOADER && typeof window.DERMA_UPLOADER.getFile === 'function') {
      var f = window.DERMA_UPLOADER.getFile();
      if (f) return { kind: 'file', value: f };
    }
    // Fallback: read directly from the file input.
    var input = document.getElementById('imageInput');
    if (input && input.files && input.files[0]) {
      return { kind: 'file', value: input.files[0] };
    }
    return null;
  }

  function getImageName() {
    if (window.DERMA_QUALITY && window.DERMA_QUALITY.getImageName) {
      return window.DERMA_QUALITY.getImageName();
    }
    var inp = document.getElementById('id_image_name');
    if (inp && inp.value.trim()) return inp.value.trim();
    var fileInput = document.getElementById('imageInput');
    if (fileInput && fileInput.files && fileInput.files[0]) {
      return fileInput.files[0].name.replace(/\.[^.]+$/, '');
    }
    return 'skin-image';
  }

  var stageTimers = [];
  var inFlight = false;
  // Per-request AbortController for the fetch-based phone-image path.
  // The native-form-submit dermoscopic path can't be aborted, but we
  // still let the user click Cancel to unlock the UI (the navigation
  // may complete later).
  var currentController = null;
  // Slow-notice timeout id — cleared when the request settles so the
  // notice only fires if the request is genuinely still in flight.
  var slowTimer = null;
  // True when the user explicitly clicked the overlay's Cancel button.
  // Used by the phone-image catch block to suppress the redundant
  // "Prediction request timed out" error message.
  var userCancelled = false;
  var SLOW_TIMEOUT_MS = 60000;

  function getSlowNotice() {
    return document.getElementById('predictionOverlaySlow');
  }

  function hideSlowNotice() {
    var slow = getSlowNotice();
    if (slow) slow.hidden = true;
    if (slowTimer) {
      clearTimeout(slowTimer);
      slowTimer = null;
    }
  }

  function showSlowNotice() {
    var slow = getSlowNotice();
    if (slow) slow.hidden = false;
  }

  function startOverlay(imageSrc) {
    var overlay = getOverlay();
    if (!overlay) return;
    overlay.hidden = false;
    overlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    var scanImage = getScanImage();
    if (scanImage && imageSrc) {
      scanImage.src = imageSrc;
      scanImage.hidden = false;
    }
    var stages = getStages();
    stageTimers.forEach(clearTimeout);
    stageTimers = [];
    [1500, 3000, 5500].forEach(function (delay, index) {
      stageTimers.push(setTimeout(function () {
        if (!stages[index] || !stages[index + 1]) return;
        stages[index].classList.remove('is-active');
        stages[index].classList.add('is-done');
        stages[index + 1].classList.add('is-active');
      }, delay));
    });
    // Arm the slow-notice timer. If the request is still in flight
    // after SLOW_TIMEOUT_MS, the non-blocking notice appears inside
    // the overlay (no alert()). Cleared by resetOverlay()/hideSlowNotice()
    // when the request settles.
    hideSlowNotice();
    slowTimer = setTimeout(function () {
      if (inFlight) showSlowNotice();
    }, SLOW_TIMEOUT_MS);
  }

  function resetOverlay() {
    var overlay = getOverlay();
    if (!overlay) return;
    overlay.hidden = true;
    overlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    var scanImage = getScanImage();
    if (scanImage) {
      scanImage.removeAttribute('src');
      scanImage.hidden = true;
    }
    hideSlowNotice();
    var stages = getStages();
    stages.forEach(function (stage, index) {
      stage.classList.remove('is-active', 'is-done');
      if (index === 0) stage.classList.add('is-active');
    });
    stageTimers.forEach(clearTimeout);
    stageTimers = [];
  }

  // ---- Metadata modal ----------------------------------------------------

  function getModal() {
    return document.getElementById('phoneMetadataModal');
  }

  function openModal(imageSrc) {
    var modal = getModal();
    if (!modal) return;
    modal.hidden = false;
    modal.setAttribute('aria-hidden', 'false');
    // Remember the image source the user is about to predict on, so the
    // modal's submit handler can rebuild FormData for the right image.
    modal.dataset.imageSrc = imageSrc || '';
    document.body.style.overflow = 'hidden';
    var firstInput = modal.querySelector('input, select');
    if (firstInput) firstInput.focus();
  }

  function closeModal() {
    var modal = getModal();
    if (!modal) return;
    modal.hidden = true;
    modal.setAttribute('aria-hidden', 'true');
    if (!inFlight) {
      document.body.style.overflow = '';
    }
  }

  function showError(message) {
    var dermoErr = document.getElementById('qualityPredictionTransferError')
      || document.querySelector('.medical-disclaimer[data-i18n="pg.transfer_error"]');
    if (dermoErr) {
      dermoErr.textContent = message ||
        t('pg.transfer_error', 'The image could not be prepared for prediction. Please try uploading it again.');
      dermoErr.hidden = false;
    } else {
      // Last resort: surface the error in the existing upload-form error slot.
      alert(message);
    }
  }

  function dataUrlToBlob(dataUrl) {
    var match = dataUrl.match(/^data:(image\/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=]+)$/);
    if (!match) return null;
    var binary = atob(match[2]);
    var bytes = new Uint8Array(binary.length);
    for (var i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return new Blob([bytes], { type: match[1] });
  }

  function buildPhoneFilename(stem) {
    var src = getImageSource();
    var ext = 'jpg';
    if (src && src.kind === 'file') {
      var name = src.value.name || '';
      var m = name.match(/\.(jpe?g|png|webp)$/i);
      if (m) ext = m[1].toLowerCase().replace('jpeg', 'jpg');
    } else if (src && src.kind === 'dataUrl') {
      var mm = src.value.match(/^data:image\/(jpeg|png|webp);/);
      if (mm) ext = mm[1].toLowerCase().replace('jpeg', 'jpg');
    }
    return stem + '.' + ext;
  }

  function disableButtons(disabled) {
    var ids = ['submitBtnDermo', 'submitBtnPhone', 'qualityRunDermo', 'qualityRunPhone'];
    ids.forEach(function (id) {
      var b = document.getElementById(id);
      if (b) b.disabled = disabled;
    });
  }

  // ---- Phone-image submission via fetch -----------------------------------

  async function submitPhonePrediction(metadata) {
    if (inFlight) return;
    var src = getImageSource();
    if (!src) {
      showError(t('pg.transfer_error', 'No image is selected. Please upload an image first.'));
      return;
    }
    inFlight = true;
    disableButtons(true);
    var imageSrcForOverlay;
    var blob;
    var filename;
    var stem = (getImageName() || 'phone-image').replace(/[\\/]/g, '_').replace(/\.[^.]+$/, '') || 'phone-image';
    if (window.DERMA_QUALITY) {
      var customized = window.DERMA_QUALITY.getCustomized();
      var enhanced = window.DERMA_QUALITY.getEnhanced();
      var suffix = customized ? '-customized' : (enhanced ? '-enhanced' : '');
      stem = stem + suffix;
    }
    filename = buildPhoneFilename(stem);

    if (src.kind === 'file') {
      blob = src.value;
      imageSrcForOverlay = URL.createObjectURL(blob);
    } else {
      blob = dataUrlToBlob(src.value);
      imageSrcForOverlay = src.value;
      if (!blob) {
        inFlight = false;
        disableButtons(false);
        showError();
        return;
      }
    }

    var form = document.getElementById('qualityPhoneForm');
    var actionUrl = form ? form.getAttribute('action') :
      (window.DERMA && window.DERMA.phonePredictUrl
        ? window.DERMA.phonePredictUrl : '/predict/phone-image/');
    var formData = new FormData();
    if (form) {
      // Pull CSRF + any hidden inputs that already exist on the form.
      Array.prototype.forEach.call(form.querySelectorAll('input[type="hidden"]'), function (inp) {
        if (inp.name && inp.name !== 'image' && inp.name !== 'image_name'
            && inp.name !== 'patient_id' && inp.name !== 'age'
            && inp.name !== 'sex' && inp.name !== 'lesion_location') {
          formData.append(inp.name, inp.value);
        }
      });
    }
    formData.set('image_name', getImageName());
    if (metadata.patient_id) formData.set('patient_id', metadata.patient_id);
    if (metadata.age !== undefined && metadata.age !== '') formData.set('age', metadata.age);
    if (metadata.sex) formData.set('sex', metadata.sex);
    if (metadata.lesion_location) formData.set('lesion_location', metadata.lesion_location);
    formData.append('image', blob, filename);

    startOverlay(imageSrcForOverlay);
    // Assign the controller to the module-level currentController so
    // cancelInFlight() (called by the overlay's Cancel button) can abort
    // this fetch when the user gives up waiting.
    currentController = window.AbortController ? new AbortController() : null;
    var controller = currentController;
    // Hard cap at 120s — at that point we treat it as a real failure
    // (not a slow-notice) and surface the network error.
    var timeoutId = setTimeout(function () {
      if (controller) controller.abort();
    }, 120000);
    try {
      var response = await fetch(actionUrl, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        signal: controller ? controller.signal : undefined,
      });
      clearTimeout(timeoutId);
      currentController = null;
      if (response.redirected || (response.ok && response.url && response.url !== actionUrl)) {
        window.location.assign(response.url);
        return;
      }
      // Server returned the upload page with an error message — surface it.
      var html = await response.text();
      var doc = new DOMParser().parseFromString(html, 'text/html');
      var msg = doc.querySelector('.medical-disclaimer [data-i18n-server]')
        || doc.querySelector('.medical-disclaimer p');
      resetOverlay();
      inFlight = false;
      disableButtons(false);
      closeModal();
      showError(msg ? msg.textContent.trim() : undefined);
    } catch (err) {
      clearTimeout(timeoutId);
      currentController = null;
      resetOverlay();
      inFlight = false;
      disableButtons(false);
      closeModal();
      // If the user explicitly clicked Cancel, don't show an extra
      // error — they already know. Otherwise surface the abort/network
      // message.
      var isAbort = err && err.name === 'AbortError';
      if (!isAbort || !userCancelled) {
        var msg = isAbort
          ? t('pg.transfer_timeout', 'Prediction request timed out. Please try again.')
          : t('pg.transfer_network_error', 'Image upload failed. Check your connection and try again.');
        showError(msg);
      }
      userCancelled = false;
    }
  }

  // ---- Dermoscopic submission (native form POST + overlay) -----------------

  function wireDermoButton(btnId, hiddenFormId) {
    var btn = document.getElementById(btnId);
    if (!btn) return;
    btn.addEventListener('click', function (e) {
      if (inFlight) { e.preventDefault(); return; }
      var src = getImageSource();
      if (!src) {
        showError(t('pg.transfer_error', 'No image is selected. Please upload an image first.'));
        e.preventDefault();
        return;
      }
      var overlaySrc;
      var blob;
      var stem = (getImageName() || 'skin-image').replace(/[\\/]/g, '_').replace(/\.[^.]+$/, '') || 'skin-image';
      var customized = !!(window.DERMA_QUALITY && window.DERMA_QUALITY.getCustomized());
      var enhanced = !!(window.DERMA_QUALITY && window.DERMA_QUALITY.getEnhanced());
      var suffix = customized ? '-customized' : (enhanced ? '-enhanced' : '');

      if (src.kind === 'file') {
        blob = src.value;
        overlaySrc = URL.createObjectURL(blob);
        // Build or update the hidden form so it carries the file.
        var form = document.getElementById(hiddenFormId);
        if (!form) {
          // Upload page: the visible uploadForm already has the file.
          if (btn.getAttribute('type') === 'submit') {
            // Native form submit handles it — let the click fall through.
            inFlight = true;
            disableButtons(true);
            startOverlay(overlaySrc);
            scheduleSafetyNet();
            return;
          }
          showError(t('pg.transfer_error',
            'Could not find the dermoscopic prediction form. Please reload the page.'));
          e.preventDefault();
          return;
        }
        // Quality-check page: populate the hidden form with a fresh Blob.
        var filename = stem + suffix + '.' + (blob.name.match(/\.(\w+)$/)||[,'jpg'])[1];
        // Clear any prior file inputs we may have injected.
        Array.prototype.forEach.call(form.querySelectorAll('input[type="file"]'), function (n) { n.remove(); });
        var fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.name = 'image';
        fileInput.hidden = true;
        var dt = new DataTransfer();
        dt.items.add(new File([blob], filename, { type: blob.type || 'image/jpeg' }));
        fileInput.files = dt.files;
        form.appendChild(fileInput);
        var nameInput = form.querySelector('input[name="image_name"]');
        if (nameInput) nameInput.value = getImageName();
        inFlight = true;
        disableButtons(true);
        startOverlay(overlaySrc);
        scheduleSafetyNet();
        // Submit natively — this navigates the browser to the result page.
        form.submit();
        e.preventDefault();
      } else {
        // data: URL — quality-check page hands us a base64 string.
        blob = dataUrlToBlob(src.value);
        if (!blob) {
          showError();
          e.preventDefault();
          return;
        }
        overlaySrc = src.value;
        var form2 = document.getElementById(hiddenFormId);
        if (!form2) {
          showError(t('pg.transfer_error', 'Could not find the dermoscopic prediction form.'));
          e.preventDefault();
          return;
        }
        // Build the image as a real File and append it to the hidden form.
        Array.prototype.forEach.call(form2.querySelectorAll('input[type="file"]'), function (n) { n.remove(); });
        var fileInput2 = document.createElement('input');
        fileInput2.type = 'file';
        fileInput2.name = 'image';
        fileInput2.hidden = true;
        var dt2 = new DataTransfer();
        var ext2 = (src.value.match(/^data:image\/(jpeg|png|webp);/) || [,'jpeg'])[1].replace('jpeg','jpg');
        dt2.items.add(new File([blob], stem + suffix + '.' + ext2, { type: blob.type }));
        fileInput2.files = dt2.files;
        form2.appendChild(fileInput2);
        var nameInput2 = form2.querySelector('input[name="image_name"]');
        if (nameInput2) nameInput2.value = getImageName();
        inFlight = true;
        disableButtons(true);
        startOverlay(overlaySrc);
        scheduleSafetyNet();
        form2.submit();
        e.preventDefault();
      }
    });
  }

  // `scheduleSafetyNet()` used to be a hard 60s timeout that fired
  // alert('The prediction is taking longer than expected...') and reset
  // the UI. That was wrong: it (a) blocked the page with a modal alert,
  // (b) lied — "Please try again" — even though the request was still
  // legitimately running on Render's free tier, and (c) hid the overlay
  // while the request was still in flight, leaving the user confused.
  //
  // The slow-notice is now armed inside startOverlay() and shows a
  // non-blocking amber notice inside the overlay itself. scheduleSafetyNet()
  // is retained as a no-op for backwards compatibility with any caller
  // that still invokes it, but it no longer does anything destructive.
  function scheduleSafetyNet() {
    /* intentionally a no-op — see comment above. */
  }

  function cancelInFlight() {
    if (!inFlight) return;
    // Mark the cancellation so the phone-image catch block doesn't pop
    // a redundant "Prediction request timed out" error — the user already
    // knows; they clicked Cancel.
    userCancelled = true;
    // Abort the fetch-based phone-image request if one is active.
    if (currentController) {
      try { currentController.abort(); } catch (e) { /* ignore */ }
      currentController = null;
    }
    inFlight = false;
    disableButtons(false);
    resetOverlay();
  }

  // Expose a tiny public API so the Cancel button in the overlay can
  // call back into the dual-prediction controller.
  window.DERMA_DUAL = {
    cancelInFlight: cancelInFlight,
  };

  // ---- Phone button → open modal -----------------------------------------

  function wirePhoneButton(btnId) {
    var btn = document.getElementById(btnId);
    if (!btn) return;
    btn.addEventListener('click', function () {
      if (inFlight) return;
      var src = getImageSource();
      if (!src) {
        showError(t('pg.transfer_error', 'No image is selected. Please upload an image first.'));
        return;
      }
      openModal(src.kind === 'file' ? URL.createObjectURL(src.value) : src.value);
    });
  }

  function wireModal() {
    var modal = getModal();
    if (!modal) return;
    var closeBtn = document.getElementById('phoneMetadataClose');
    var cancelBtn = document.getElementById('phoneMetadataCancel');
    var form = document.getElementById('phoneMetadataForm');
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', function (e) {
      if (e.target === modal) closeModal();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !modal.hidden && !inFlight) closeModal();
    });
    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var data = {
          patient_id: (form.querySelector('[name="patient_id"]') || {}).value || '',
          age: (form.querySelector('[name="age"]') || {}).value || '',
          sex: (form.querySelector('[name="sex"]') || {}).value || '',
          lesion_location: (form.querySelector('[name="lesion_location"]') || {}).value || '',
        };
        submitPhonePrediction(data);
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    wireDermoButton('submitBtnDermo', null);   // upload page: native submit
    wireDermoButton('qualityRunDermo', 'qualityDermoForm'); // quality page
    wirePhoneButton('submitBtnPhone');
    wirePhoneButton('qualityRunPhone');
    wireModal();
    // Wire up the overlay's Cancel button. It calls back into
    // cancelInFlight() (exposed on window.DERMA_DUAL) which aborts the
    // active fetch and unlocks the UI.
    var overlayCancel = document.getElementById('predictionOverlayCancel');
    if (overlayCancel) {
      overlayCancel.addEventListener('click', function () {
        if (window.DERMA_DUAL && typeof window.DERMA_DUAL.cancelInFlight === 'function') {
          window.DERMA_DUAL.cancelInFlight();
        }
      });
    }
  });
})();
