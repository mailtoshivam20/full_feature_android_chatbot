import { useCallback, useRef, useState } from "react";

interface Props {
  onTranscript: (text: string) => void;
}

declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}

const SpeechRecognitionAPI =
  typeof window !== "undefined"
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null;

export default function VoiceInput({ onTranscript }: Props) {
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  const toggle = useCallback(() => {
    if (!SpeechRecognitionAPI) return;

    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    const recognition = new SpeechRecognitionAPI();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      onTranscript(transcript);
    };
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    recognition.start();
    recognitionRef.current = recognition;
    setListening(true);
  }, [listening, onTranscript]);

  if (!SpeechRecognitionAPI) return null;

  return (
    <button
      onClick={toggle}
      className={`p-1.5 rounded-lg transition ${
        listening ? "bg-red-100 text-red-600 dark:bg-red-900" : "hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500"
      }`}
      title={listening ? "Stop recording" : "Voice input"}
      aria-label={listening ? "Stop recording" : "Voice input"}
    >
      {listening ? "🎙️" : "🎤"}
    </button>
  );
}
