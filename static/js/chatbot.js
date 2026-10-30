
/* ============================================
   DermaCheckerBD - Chatbot Frontend
============================================ */

(function () {
    'use strict';

    /* -----------------------------------------
       DOM Elements
    ----------------------------------------- */

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

    if (!fabBtn || !panel || !form || !messages) return;

    /* -----------------------------------------
       Chatbot Configuration
    ----------------------------------------- */

    var scope = panel.getAttribute('data-chat-scope') || 'public';
    var scopeType = panel.getAttribute('data-chat-role') || 'public';

    var historyKey = 'derma_chat_history_' + scope;

    var messageUrl =
        panel.getAttribute('data-message-url') || '/chatbot/message/';

    var isAnonymous = (scopeType === 'public');

    var history = [];

    var isSending = false;

    var lastFocusedEl = null;

    /* -----------------------------------------
       Translation Helper
    ----------------------------------------- */

    function translate(key, fallback) {
        if (window.DERMA && typeof window.DERMA.t === 'function') {
            return window.DERMA.t(key, fallback);
        }

        return fallback;
    }

    /* -----------------------------------------
       Welcome Message
    ----------------------------------------- */

    function welcomeMessage() {

        var key = scopeType === 'staff'
            ? 'chatbot.welcome_staff'
            : (
                scopeType === 'public'
                    ? 'chatbot.welcome_public'
                    : 'chatbot.welcome_private'
            );

        var fallback = scopeType === 'staff'
            ? 'I can answer public site questions and provide anonymized site-wide totals. I cannot access usernames or individual records.'

            : (
                scopeType === 'public'
                    ? 'I can answer 7 predefined questions for guests. Tap a button below, or sign in for detailed personalized answers. I don\'t diagnose.'

                    : 'I can answer public site questions and summarize your own dashboard and history. I cannot access another user\'s records. I don\'t diagnose.'
            );

        return translate(key, fallback);
    }

    /* -----------------------------------------
       Load Conversation History
    ----------------------------------------- */

    try {
        var saved = sessionStorage.getItem(historyKey);

        if (saved) {
            history = JSON.parse(saved);
        }

    } catch (e) {
        history = [];
    }

    if (!Array.isArray(history)) {
        history = [];
    }

    history = history.filter(function (m) {

        return (
            m &&
            (m.role === 'user' || m.role === 'model') &&
            typeof m.content === 'string'
        );

    }).slice(-20);

    /* -----------------------------------------
       Save History
    ----------------------------------------- */

    function persist() {

        try {
            sessionStorage.setItem(
                historyKey,
                JSON.stringify(history)
            );

        } catch (e) {
            console.warn('Chat history could not be saved.');
        }
    }

    /* -----------------------------------------
       Escape HTML
    ----------------------------------------- */

    function escapeHtml(value) {

        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    /* -----------------------------------------
       Sanitize Chatbot HTML
    ----------------------------------------- */

    function sanitizeChatHtml(inputValue) {

        if (inputValue == null) {
            return '';
        }

        var html = escapeHtml(String(inputValue));

        var allowedTags = [
            'b',
            'i',
            'em',
            'strong',
            'code',
            'br',
            'ul',
            'ol',
            'li',
            'p'
        ];

        allowedTags.forEach(function (tag) {

            // Opening tags
            html = html.replace(
                new RegExp('&lt;' + tag + '\\s*&gt;', 'gi'),
                '<' + tag + '>'
            );

            // Closing tags
            html = html.replace(
                new RegExp('&lt;/' + tag + '\\s*&gt;', 'gi'),
                '</' + tag + '>'
            );

            // Self-closing tags
            html = html.replace(
                new RegExp('&lt;' + tag + '\\s*/&gt;', 'gi'),
                '<' + tag + '>'
            );

        });

        return html;
    }

    /* -----------------------------------------
       Normalize Message Content
    ----------------------------------------- */

    function normalizeMessage(content) {

        if (content == null) {
            return '';
        }

        return String(content)
            .replace(/\r\n/g, '\n')
            .replace(/\r/g, '\n')
            .replace(/\u00A0/g, ' ')
            .trim();
    }

    /* -----------------------------------------
       Append Chat Message
    ----------------------------------------- */

    function appendMessage(role, content, animate) {

        var cleanContent = normalizeMessage(content);

        if (!cleanContent) return null;

        var wrap = document.createElement('div');

        wrap.className = 'chatbot-msg ' +
            (role === 'user' ? 'user' : 'chatbot-msg-bot');

        wrap.setAttribute(
            'data-role',
            role === 'user' ? 'user' : 'bot'
        );

        var bubble = document.createElement('div');

        bubble.className = 'chatbot-msg-bubble';

        bubble.style.textAlign =
            role === 'user' ? 'right' : 'left';

        // Safe HTML rendering
        bubble.innerHTML = sanitizeChatHtml(cleanContent);

        // Remove default paragraph margins
        bubble.querySelectorAll('p').forEach(function (p) {

            p.style.margin = '0 0 6px';

            if (
                !p.textContent.trim() &&
                !p.querySelector('br')
            ) {
                p.remove();
            }

        });

        // Avoid empty list spacing
        bubble.querySelectorAll('ul, ol').forEach(function (list) {

            if (!list.children.length) {
                list.remove();
            }

        });

        wrap.appendChild(bubble);

        messages.appendChild(wrap);

        messages.scrollTop = messages.scrollHeight;

        return wrap;
    }

    /* -----------------------------------------
       Welcome Message + Initial FAQs
    ----------------------------------------- */

    function renderWelcome() {

        var existingWelcome = messages.querySelector(
            '.chatbot-initial-welcome'
        );

        if (existingWelcome) {
            existingWelcome.remove();
        }

        var wrap = document.createElement('div');

        wrap.className = 'chatbot-msg chatbot-msg-bot chatbot-initial-welcome';

        wrap.setAttribute('data-role', 'bot');

        var bubble = document.createElement('div');

        bubble.className = 'chatbot-msg-bubble';

        bubble.style.textAlign = 'left';

        bubble.textContent = normalizeMessage(welcomeMessage());

        wrap.appendChild(bubble);

        messages.appendChild(wrap);
    }

    /* -----------------------------------------
       Restore Saved History
    ----------------------------------------- */

    if (history.length) {

        // Remove the server-rendered welcome message.
        var initialWelcome = messages.querySelector(
            '.chatbot-msg-bot .chatbot-msg-bubble'
        );

        if (initialWelcome) {
            initialWelcome.closest('.chatbot-msg').remove();
        }

        history.forEach(function (m) {

            appendMessage(
                m.role,
                m.content,
                false
            );

        });

        messages.scrollTop = messages.scrollHeight;
    }

    /* -----------------------------------------
       Typing Animation
    ----------------------------------------- */

    function appendTyping() {

        var wrap = document.createElement('div');

        wrap.className = 'chatbot-msg chatbot-msg-bot';

        wrap.setAttribute('data-role', 'bot');

        var bubble = document.createElement('div');

        bubble.className = 'chatbot-msg-bubble';

        bubble.innerHTML =
            '<div class="chatbot-typing">' +
                '<span></span>' +
                '<span></span>' +
                '<span></span>' +
            '</div>';

        wrap.appendChild(bubble);

        messages.appendChild(wrap);

        messages.scrollTop = messages.scrollHeight;

        return wrap;
    }

    /* -----------------------------------------
       FAQ Rendering
    ----------------------------------------- */

    function appendFaqs(faqs) {

        var existing = document.getElementById('chatbotFaqs');

        if (existing) {
            existing.remove();
        }

        if (!faqs || !faqs.length) {
            return;
        }

        var wrap = document.createElement('div');

        wrap.className = 'chatbot-faqs';

        wrap.id = 'chatbotFaqs';

        wrap.setAttribute('role', 'group');

        wrap.setAttribute(
            'aria-label',
            'Frequently asked questions'
        );

        faqs.forEach(function (faq) {

            var btn = document.createElement('button');

            btn.type = 'button';

            btn.className = 'chatbot-faq-btn';

            btn.setAttribute('data-faq-id', faq.id);

            btn.setAttribute(
                'data-faq-question',
                faq.question
            );

            btn.textContent = faq.question;

            btn.addEventListener('click', function () {

                sendFaq(
                    faq.id,
                    faq.question
                );

            });

            wrap.appendChild(btn);

        });

        messages.appendChild(wrap);

        messages.scrollTop = messages.scrollHeight;
    }

    /* -----------------------------------------
       Initial FAQ Button Events
    ----------------------------------------- */

    function bindInitialFaqs() {

        if (!faqsContainer) return;

        var buttons = faqsContainer.querySelectorAll(
            '.chatbot-faq-btn'
        );

        buttons.forEach(function (btn) {

            btn.addEventListener('click', function () {

                var faqId = btn.getAttribute('data-faq-id');

                var faqQuestion =
                    btn.getAttribute('data-faq-question') ||
                    btn.textContent;

                sendFaq(
                    faqId,
                    faqQuestion
                );

            });

        });
    }

    bindInitialFaqs();

    /* -----------------------------------------
       Open Chatbot
    ----------------------------------------- */

    function openPanel() {

        panel.hidden = false;

        panel.setAttribute('aria-modal', 'true');

        fabBtn.setAttribute('aria-expanded', 'true');

        lastFocusedEl = document.activeElement;

        setTimeout(function () {

            if (input && !input.disabled) {
                input.focus();
            }

        }, 100);

        document.addEventListener(
            'focus',
            trapFocus,
            true
        );
    }

    /* -----------------------------------------
       Close Chatbot
    ----------------------------------------- */

    function closePanel() {

        panel.hidden = true;

        panel.setAttribute('aria-modal', 'false');

        fabBtn.setAttribute('aria-expanded', 'false');

        document.removeEventListener(
            'focus',
            trapFocus,
            true
        );

        if (
            lastFocusedEl &&
            typeof lastFocusedEl.focus === 'function'
        ) {
            lastFocusedEl.focus();
        }
    }

    /* -----------------------------------------
       Focus Management
    ----------------------------------------- */

    var FOCUSABLE =
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

    function trapFocus(e) {

        if (panel.hidden) return;

        if (!panel.contains(e.target)) {

            e.stopPropagation();

            if (input) {
                input.focus();
            }

        }
    }

    panel.addEventListener('keydown', function (e) {

        if (e.key !== 'Tab' || panel.hidden) {
            return;
        }

        var focusable = Array.prototype.filter.call(
            panel.querySelectorAll(FOCUSABLE),
            function (el) {

                return (
                    el.offsetParent !== null &&
                    !el.disabled
                );

            }
        );

        if (!focusable.length) return;

        var first = focusable[0];

        var last = focusable[focusable.length - 1];

        if (
            e.shiftKey &&
            document.activeElement === first
        ) {

            e.preventDefault();

            last.focus();

        } else if (
            !e.shiftKey &&
            document.activeElement === last
        ) {

            e.preventDefault();

            first.focus();

        }

    });

    /* -----------------------------------------
       Button Events
    ----------------------------------------- */

    fabBtn.addEventListener('click', function () {

        if (panel.hidden) {
            openPanel();
        } else {
            closePanel();
        }

    });

    if (closeBtn) {

        closeBtn.addEventListener(
            'click',
            closePanel
        );

    }

    /* -----------------------------------------
       Clear Conversation
    ----------------------------------------- */

    if (clearBtn) {

        clearBtn.addEventListener('click', function () {

            if (isSending) return;

            history = [];

            persist();

            messages.innerHTML = '';

            renderWelcome();

            // Restore guest FAQ buttons from original server HTML.
            if (isAnonymous && faqsContainer) {

                var faqs = [];

                faqsContainer.querySelectorAll(
                    '.chatbot-faq-btn'
                ).forEach(function (btn) {

                    faqs.push({

                        id: btn.getAttribute('data-faq-id'),

                        question:
                            btn.getAttribute('data-faq-question') ||
                            btn.textContent.trim()

                    });

                });

                appendFaqs(faqs);
            }

            messages.scrollTop = 0;

        });

    }

    /* -----------------------------------------
       Escape Key
    ----------------------------------------- */

    document.addEventListener('keydown', function (e) {

        if (
            e.key === 'Escape' &&
            !panel.hidden
        ) {
            closePanel();
        }

    });

    /* -----------------------------------------
       CSRF Protected API Request
    ----------------------------------------- */

    function postMessage(payload) {

        var csrfInput = document.getElementById(
            'chatbotCsrf'
        );

        return fetch(messageUrl, {

            method: 'POST',

            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfInput
                    ? csrfInput.value
                    : ''
            },

            body: JSON.stringify(payload),

            credentials: 'same-origin'

        }).then(function (response) {

            if (!response.ok) {

                throw new Error(
                    'HTTP ' + response.status
                );

            }

            return response.json();

        });
    }

    /* -----------------------------------------
       Send FAQ
    ----------------------------------------- */

    function sendFaq(faqId, faqQuestion) {

        if (!faqId || isSending) return;

        var question = normalizeMessage(faqQuestion);

        if (!question) return;

        isSending = true;

        appendMessage(
            'user',
            question,
            true
        );

        history.push({

            role: 'user',

            content: question

        });

        history = history.slice(-20);

        persist();

        var faqsBar = document.getElementById(
            'chatbotFaqs'
        );

        if (faqsBar) {
            faqsBar.style.display = 'none';
        }

        var typing = appendTyping();

        postMessage({

            faq_id: faqId,

            language:
                (window.DERMA && window.DERMA.language) || 'en'

        })

        .then(function (data) {

            typing.remove();

            var reply = data.reply || translate(
                'chatbot.no_reply',
                '(no reply)'
            );

            appendMessage(
                'model',
                reply,
                true
            );

            history.push({

                role: 'model',

                content: reply

            });

            history = history.slice(-20);

            persist();

        })

        .catch(function (err) {

            typing.remove();

            var errorMessage = translate(
                'chatbot.error.network',
                'Sorry, I couldn\'t reach the assistant right now. Please try again in a moment. For urgent concerns, consult a dermatologist.'
            );

            appendMessage(
                'model',
                errorMessage,
                true
            );

            history.push({

                role: 'model',

                content: errorMessage

            });

            history = history.slice(-20);

            persist();

            console.error(
                'DermaCheckerBD chatbot FAQ request failed:',
                err
            );

        })

        .finally(function () {

            isSending = false;

            if (isAnonymous) {

                var faqsBar2 = document.getElementById(
                    'chatbotFaqs'
                );

                if (faqsBar2) {
                    faqsBar2.style.display = '';
                }

            }

            if (input) {
                input.focus();
            }

        });
    }

    /* -----------------------------------------
       Send Normal Message
    ----------------------------------------- */

    form.addEventListener('submit', async function (e) {

        e.preventDefault();

        if (isSending) return;

        var text = normalizeMessage(input.value);

        if (!text) return;

        isSending = true;

        appendMessage(
            'user',
            text,
            true
        );

        history.push({

            role: 'user',

            content: text

        });

        history = history.slice(-20);

        persist();

        input.value = '';

        input.disabled = true;

        if (sendBtn) {
            sendBtn.disabled = true;
        }

        var faqsBar = document.getElementById(
            'chatbotFaqs'
        );

        if (faqsBar) {
            faqsBar.style.display = 'none';
        }

        var typing = appendTyping();

        try {

            var data = await postMessage({

                message: text,

                language:
                    (window.DERMA && window.DERMA.language) || 'en',

                history: history.slice(0, -1)

            });

            typing.remove();

            var reply = data.reply || translate(
                'chatbot.no_reply',
                '(no reply)'
            );

            appendMessage(
                'model',
                reply,
                true
            );

            history.push({

                role: 'model',

                content: reply

            });

            history = history.slice(-20);

            persist();

            if (
                isAnonymous &&
                data.faqs &&
                data.faqs.length
            ) {

                appendFaqs(data.faqs);

            }

        } catch (err) {

            typing.remove();

            var errorMessage = translate(
                'chatbot.error.network',
                'Sorry, I couldn\'t reach the assistant right now. Please try again in a moment. For urgent concerns, consult a dermatologist.'
            );

            appendMessage(
                'model',
                errorMessage,
                true
            );

            history.push({

                role: 'model',

                content: errorMessage

            });

            history = history.slice(-20);

            persist();

            console.error(
                'DermaCheckerBD chatbot request failed:',
                err
            );

        } finally {

            isSending = false;

            input.disabled = false;

            if (sendBtn) {
                sendBtn.disabled = false;
            }

            if (isAnonymous) {

                var faqsBar2 = document.getElementById(
                    'chatbotFaqs'
                );

                if (faqsBar2) {
                    faqsBar2.style.display = '';
                }

            }

            input.focus();

        }

    });

    /* -----------------------------------------
       End of Chatbot
    ----------------------------------------- */

})();
