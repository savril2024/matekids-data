/**
 * assets/js/tts.js
 * Texto a voz usando Web Speech API (solo para navegador).
 * Compatible con Chrome, Edge, Safari, Firefox.
 */
window.MateKidsTTS = {
    _isSpeaking: false,

    isSupported: function () {
        return 'speechSynthesis' in window;
    },

    speak: function (text, lang, rate) {
        if (!this.isSupported()) {
            return 'not_supported';
        }

        // Cancelar cualquier narración anterior
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang === 'es' ? 'es-ES' : 'en-US';
        utterance.rate = rate || 0.85;
        utterance.pitch = 1.1;
        utterance.volume = 1.0;

        // Intentar usar una voz en español si está disponible
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(v => 
            v.lang.startsWith(lang === 'es' ? 'es' : 'en')
        );
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }

        this._isSpeaking = true;

        utterance.onend = () => {
            this._isSpeaking = false;
        };

        utterance.onerror = (e) => {
            console.warn('TTS error:', e);
            this._isSpeaking = false;
        };

        window.speechSynthesis.speak(utterance);
        return 'ok';
    },

    stop: function () {
        window.speechSynthesis.cancel();
        this._isSpeaking = false;
    },

    isSpeaking: function () {
        return this._isSpeaking;
    }
};

// Precargar voces
if ('speechSynthesis' in window) {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
    };
}