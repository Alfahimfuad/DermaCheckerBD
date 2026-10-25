
/* DermaCheckerBD — chatbot frontend */

(function () {
    'use strict';

    var fabBtn = document.getElementById('chatbotToggle');
    var fab = document.getElementById('chatbotFab');
    var panel = document.getElementById('chatbotPanel');
    var closeBtn = document.getElementById('chatbotClose');
    var clearBtn = document.getElementById('chatbotClear');
    var form = document.getElementById('chatbotForm');
    var input = document.getElementById('chatbotInput');
    var sendBtn = document.getElementById('chatbotSend');
    var messages = document.getElementById('chatbotMessages');
    var faqsContainer = document.getElementById('chatbotFaqs');

    if (!fabBtn || !panel || !form) return;

    var scope = panel.getAttribute('data-chat-scope') || 'public';
    var scopeType = panel.getAttribute('data-chat-role') || 'public';
    var historyKey = 'derma_chat_history_' + scope;
    var messageUrl = panel.getAttribute('data-message-url') || '/chatbot/message/';

    // True when the visitor is NOT signed in. Anonymous users get FAQ-only
    // replies and the chatbot will never call Gemini on their behalf.
    var isAnonymous = (scopeType === 'public');

    // Conversation held in JS only; lives for the current page session.
    // We persist in sessionStorage so it survives page navigations.
    var history = [];

    try {
        var saved = sessionStorage.getItem(historyKey);
        if (saved) history = JSON.parse(saved);
    } catch (e) {
        /* ignore */
    }

    if (!Array.isArray(history)) history = [];

    history = history.filter(function (m) {
        return (
            m &&
            (m.role === 'user' || m.role === 'model') &&
            typeof m.content === 'string'
        );
    }).slice(-20);

    if (history.length) {
        // Re-render history (skip the welcome bubble already in DOM)
        history.forEach(function (m) {
            appendMessage(m.role, m.content, false);
        });
        messages.scrollTop = messages.scrollHeight;
    }

    function persist() {
        try {
            sessionStorage.setItem(historyKey, JSON.stringify(history));
        } catch (e) {}
    }

    function welcomeMessage() {
        var key = scopeType === 'staff'
            ? 'chatbot.welcome_staff'
            : (scopeType === 'public'
                ? 'chatbot.welcome_public'
                : 'chatbot.welcome_private');

        var fallback = scopeType === 'staff'
            ? 'I can answer public site questions and provide anonymized site-wide totals. I cannot access usernames or individual records.'
            : (scopeType === 'public'
                ? 'I can answer 7 predefined questions for guests. Tap a button below, or sign in for detailed personalized answers. I don\'t diagnose.'
                : 'I can answer public site questions and summarize your own dashboard and history. I cannot access another user\'s records. I don\'t diagnose.');

        return window.DERMA.t(key, fallback);
    }

    function appendMessage(role, content, animate) {
        var wrap = document.createElement('div');
        // Strict role → class mapping keeps user/right and bot/left alignment
        // unambiguous. The CSS relies on these exact class names.
        wrap.className = 'chatbot-msg ' + (role === 'user' ? 'user' : 'chatbot-msg-bot');
        wrap.setAttribute('data-role', role === 'user' ? 'user' : 'bot');

        var bubble = document.createElement('div');
        bubble.className = 'chatbot-msg-bubble';
        // Force a sensible text-align per role so long Bangla/English lines
        // stay right-aligned for the user and left-aligned for the bot.
        bubble.style.textAlign = role === 'user' ? 'right' : 'left';

        // Never trust downstream content as raw HTML.
        bubble.innerHTML = sanitizeChatHtml(content);

        wrap.appendChild(bubble);
        messages.appendChild(wrap);
        messages.scrollTop = messages.scrollHeight;

        return wrap;
    }

    function appendTyping() {
        var wrap = document.createElement('div');
        wrap.className = 'chatbot-msg chatbot-msg-bot';
        wrap.setAttribute('data-role', 'bot');

        var bubble = document.createElement('div');
        bubble.className = 'chatbot-msg-bubble';
        bubble.style.textAlign = 'left';
        bubble.innerHTML = '<div class="chatbot-typing"><span></span><span></span><span></span></div>';

        wrap.appendChild(bubble);
        messages.appendChild(wrap);
        messages.scrollTop = messages.scrollHeight;

        return wrap;
    }

    function appendFaqs(faqs) {
        // Remove any existing FAQ bar first (the guidance response can re-add it).
        var existing = document.getElementById('chatbotFaqs');
        if (existing) existing.remove();

        if (!faqs || !faqs.length) return;

        var wrap = document.createElement('div');
        wrap.className = 'chatbot-faqs';
        wrap.id = 'chatbotFaqs';
        wrap.setAttribute('role', 'group');
        wrap.setAttribute('aria-label', 'Frequently asked questions');

        faqs.forEach(function (faq) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'chatbot-faq-btn';
            btn.setAttribute('data-faq-id', faq.id);
            btn.setAttribute('data-faq-question', faq.question);
            btn.textContent = faq.question;
            btn.addEventListener('click', function () {
                sendFaq(faq.id, faq.question);
            });
            wrap.appendChild(btn);
        });

        messages.appendChild(wrap);
        messages.scrollTop = messages.scrollHeight;
    }

    // Wire up the server-rendered FAQ buttons (initial page load).
    if (faqsContainer) {
        var buttons = faqsContainer.querySelectorAll('.chatbot-faq-btn');
        buttons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                var faqId = btn.getAttribute('data-faq-id');
                var faqQuestion = btn.getAttribute('data-faq-question') || btn.textContent;
                sendFaq(faqId, faqQuestion);
            });
        });
    }

    var lastFocusedEl = null;

    function openPanel() {
        panel.hidden = false;
        panel.setAttribute('aria-modal', 'true');
        fabBtn.setAttribute('aria-expanded', 'true');

        lastFocusedEl = document.activeElement;

        setTimeout(function () {
            input.focus();
        }, 100);

        document.addEventListener('focus', trapFocus, true);
    }

    function closePanel() {
        panel.hidden = true;
        panel.setAttribute('aria-modal', 'false');
        fabBtn.setAttribute('aria-expanded', 'false');

        document.removeEventListener('focus', trapFocus, true);

        if (lastFocusedEl && typeof lastFocusedEl.focus === 'function') {
            lastFocusedEl.focus();
        }
    }

    // Minimal focus trap: keep Tab cycling inside the panel while it is open.
    var FOCUSABLE = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

    function trapFocus(e) {
        if (panel.hidden) return;

        if (!panel.contains(e.target)) {
            e.stopPropagation();
            input.focus();
        }
    }

    panel.addEventListener('keydown', function (e) {
        if (e.key !== 'Tab' || panel.hidden) return;

        var f = Array.prototype.filter.call(
            panel.querySelectorAll(FOCUSABLE),
            function (el) {
                return el.offsetParent !== null && !el.disabled;
            }
        );

        if (!f.length) return;

        var first = f[0];
        var last = f[f.length - 1];

        if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
        }
    });

    fabBtn.addEventListener('click', function () {
        if (panel.hidden) {
            openPanel();
        } else {
            closePanel();
        }
    });

    if (closeBtn) {
        closeBtn.addEventListener('click', closePanel);
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', function () {
            history = [];
            persist();

            // Reset to welcome
            messages.innerHTML = '';
            appendMessage('model', welcomeMessage(), false);
            // Re-add the FAQ bar for anonymous users.
            if (isAnonymous && faqsContainer) {
                var faqs = [];
                faqsContainer.querySelectorAll('.chatbot-faq-btn').forEach(function (btn) {
                    faqs.push({
                        id: btn.getAttribute('data-faq-id'),
                        question: btn.getAttribute('data-faq-question') || btn.textContent
                    });
                });
                if (faqs.length) appendFaqs(faqs);
            }
        });
    }

    // Esc to close
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !panel.hidden) {
            closePanel();
        }
    });

    function sendFaq(faqId, faqQuestion) {
        if (!faqId) return;
        // Show the FAQ question as a user-side bubble so the conversation
        // reads naturally on both desktop and mobile.
        appendMessage('user', faqQuestion, true);
        history.push({ role: 'user', content: faqQuestion });
        history = history.slice(-20);
        persist();

        // Hide the FAQ bar while a reply is in flight so the user cannot
        // spam-click multiple buttons.
        var faqsBar = document.getElementById('chatbotFaqs');
        if (faqsBar) faqsBar.style.display = 'none';

        var typing = appendTyping();

        postMessage({ faq_id: faqId, language: (window.DERMA && window.DERMA.language) || 'en' })
            .then(function (data) {
                typing.remove();
                var reply = data.reply || window.DERMA.t('chatbot.no_reply', '(no reply)');
                appendMessage('model', reply, true);
                history.push({ role: 'model', content: reply });
                history = history.slice(-20);
                persist();
            })
            .catch(function (err) {
                typing.remove();
                var msg = window.DERMA.t(
                    'chatbot.error.network',
                    'Sorry, I couldn\'t reach the assistant right now. Please try again in a moment. For urgent concerns, consult a dermatologist.'
                );
                appendMessage('model', msg, true);
                history.push({ role: 'model', content: msg });
                history = history.slice(-20);
                persist();
                console.error('DermaCheckerBD chatbot FAQ request failed:', err);
            })
            .finally(function () {
                // Re-show the FAQ bar for anonymous users (so they can ask another).
                if (isAnonymous) {
                    var faqsBar2 = document.getElementById('chatbotFaqs');
                    if (faqsBar2) faqsBar2.style.display = '';
                }
                input.focus();
            });
    }

    function postMessage(payload) {
        var csrfInput = document.getElementById('chatbotCsrf');
        return fetch(messageUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfInput ? csrfInput.value : ''
            },
            body: JSON.stringify(payload),
            credentials: 'same-origin'
        }).then(function (resp) {
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            return resp.json();
        });
    }

    // Send message
    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        var text = input.value.trim();
        if (!text) return;

        appendMessage('user', text, true);

        history.push({
            role: 'user',
            content: text
        });

        history = history.slice(-20);
        persist();

        input.value = '';
        input.disabled = true;
        sendBtn.disabled = true;

        // Hide the FAQ bar while a reply is in flight.
        var faqsBar = document.getElementById('chatbotFaqs');
        if (faqsBar) faqsBar.style.display = 'none';

        var typing = appendTyping();

        try {
            var data = await postMessage({
                message: text,
                language: (window.DERMA && window.DERMA.language) || 'en',
                history: history.slice(0, -1)
            });

            // Replace typing bubble with reply
            typing.remove();

            var reply = data.reply || window.DERMA.t(
                'chatbot.no_reply',
                '(no reply)'
            );

            appendMessage('model', reply, true);

            history.push({
                role: 'model',
                content: reply
            });

            history = history.slice(-20);
            persist();

            // For anonymous users, the server may include a `faqs` array on
            // guidance responses so we can re-render the FAQ quick-reply bar.
            if (isAnonymous && data.faqs && data.faqs.length) {
                appendFaqs(data.faqs);
            }
        } catch (err) {
            typing.remove();

            var msg = window.DERMA.t(
                'chatbot.error.network',
                'Sorry, I couldn\'t reach the assistant right now. Please try again in a moment. For urgent concerns, consult a dermatologist.'
            );

            appendMessage('model', msg, true);

            history.push({
                role: 'model',
                content: msg
            });

            history = history.slice(-20);
            persist();

            console.error('DermaCheckerBD chatbot request failed:', err);
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            // Re-show the FAQ bar for anonymous users (so they can ask another).
            if (isAnonymous) {
                var faqsBar2 = document.getElementById('chatbotFaqs');
                if (faqsBar2) faqsBar2.style.display = '';
            }
            input.focus();
        }
    });

    function escapeHtml(s) {
        return s
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    /**
     * Strict allowlist-based HTML sanitiser for chatbot replies.
     * Allows only b, i, em, strong, code, br, ul, ol, li and p.
     * Strips attributes from allowed tags.
     */
    function sanitizeChatHtml(input) {
        if (input == null) return '';

        var s = escapeHtml(String(input));
        var allow = ['b', 'i', 'em', 'strong', 'code', 'br', 'ul', 'ol', 'li', 'p'];

        allow.forEach(function (tag) {
            // Opening tags (no attributes permitted)
            s = s.replace(
                new RegExp('&lt;' + tag + '(\\s[^&]*)?&gt;', 'gi'),
                '<' + tag + '>'
            );

            // Closing tags
            s = s.replace(
                new RegExp('&lt;/' + tag + '&gt;', 'gi'),
                '</' + tag + '>'
            );

            // Self-closing variant (mainly for br)
            s = s.replace(
                new RegExp('&lt;' + tag + '\\s*/?&gt;', 'gi'),
                '<' + tag + '>'
            );
        });

        return s;
    }
})();
