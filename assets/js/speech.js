/**
 * assets/js/speech.js
 * Comunicación segura con el navegador para reconocimiento de voz.
 * 
 * Flujo:
 * Navegador -> Web Speech API -> speech.js -> Flet (evento personalizado)
 */
(function (window) {
    "use strict";
    
    const FletSpeech = {
        _recognition: null,
        _activeReject: null,
        _isSupported: function() {
            return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
        },
        listenOnce: function(options) {
            const opts = options || {};
            const lang = opts.lang || "es-ES";
            const timeoutMs = opts.timeoutMs || 6000;
            
            if (!FletSpeech._isSupported()) {
                FletSpeech._dispatchEvent("flet-speech-error", "not_supported");
                return;
            }
            
            // Si ya hay una escucha activa, la cancelamos
            if (FletSpeech._recognition) {
                FletSpeech._safeStop();
            }
            
            const SpeechRecognitionImpl = 
                window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognitionImpl();
            
            recognition.lang = lang;
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;
            
            FletSpeech._recognition = recognition;
            
            // Manejar resultados
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                FletSpeech._dispatchEvent("flet-speech-result", transcript);
            };
            
            // Manejar errores
            recognition.onerror = (event) => {
                const error = event.error || "unknown";
                FletSpeech._dispatchEvent("flet-speech-error", error);
            };
            
            // Manejar tiempo límite
            const timeout = setTimeout(() => {
                FletSpeech._safeStop();
                FletSpeech._dispatchEvent("flet-speech-error", "timeout");
            }, timeoutMs);
            
            // Iniciar reconocimiento
            try {
                recognition.start();
            } catch (e) {
                FletSpeech._dispatchEvent("flet-speech-error", "start_failed");
            }
        },
        stop: function() {
            FletSpeech._safeStop();
        },
        _safeStop: function() {
            if (FletSpeech._recognition) {
                try {
                    FletSpeech._recognition.stop();
                } catch (e) {
                    // Ignorar errores al detener
                }
                FletSpeech._recognition = null;
            }
        },
        _dispatchEvent: function(eventName, data) {
            // Enviar evento personalizado al framework de Flet
            window.dispatchEvent(
                new CustomEvent(eventName, { detail: data })
            );
        }
    };
    
    window.FletSpeech = FletSpeech;
    
    // Registrar evento personalizado para recibir mensajes de JavaScript
    window.addEventListener("flet-speech-result", (e) => {
        // En Flet 0.86+, los eventos personalizados se manejan en Python
    });
    
    window.addEventListener("flet-speech-error", (e) => {
        // En Flet 0.86+, los eventos personalizados se manejan en Python
    });
})(window);