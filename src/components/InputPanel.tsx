import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Type, Image, Mic, Upload, X, MicOff, Loader2, Eye, Edit3, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import KaTeXRenderer from './KaTeXRenderer';
import ConfidenceMeter from './ConfidenceMeter';
import Tesseract from 'tesseract.js';

type InputMode = 'text' | 'image' | 'voice';

// Web Speech API types
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: Event & { error: string }) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

interface InputPanelProps {
  onSubmit: (data: {
    text: string;
    inputMode: InputMode;
    confidence: number;
    requiresHITL: boolean;
  }) => void;
  isProcessing: boolean;
}

const InputPanel: React.FC<InputPanelProps> = ({ onSubmit, isProcessing }) => {
  const [inputMode, setInputMode] = useState<InputMode>('text');
  const [inputText, setInputText] = useState('');
  const [extractedText, setExtractedText] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [confidence, setConfidence] = useState(1);
  const [isRecording, setIsRecording] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(true);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [speechError, setSpeechError] = useState<string | null>(null);
  const [confidenceType, setConfidenceType] = useState<'OCR' | 'ASR' | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const isRecognitionActiveRef = useRef(false);

  const inputModes = [
    { mode: 'text' as InputMode, icon: Type, label: 'Text' },
    { mode: 'image' as InputMode, icon: Image, label: 'Image' },
    { mode: 'voice' as InputMode, icon: Mic, label: 'Voice' },
  ];

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const imageUrl = URL.createObjectURL(file);
    setUploadedImage(imageUrl);
    setIsExtracting(true);

    try {
      const result = await Tesseract.recognize(file, 'eng', {
        logger: (m) => console.log(m),
      });
      
      const ocrConfidence = result.data.confidence / 100;
      const cleanedText = result.data.text.trim();
      
      setExtractedText(cleanedText);
      setInputText(cleanedText);
      setConfidence(ocrConfidence);
      setConfidenceType('OCR');
      setIsEditing(true);
    } catch (error) {
      console.error('OCR error:', error);
      setConfidence(0);
    } finally {
      setIsExtracting(false);
    }
  };

  // Initialize Web Speech API
  const initSpeechRecognition = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setSpeechError('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
      return null;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      isRecognitionActiveRef.current = true;
      setIsRecording(true);
      setSpeechError(null);
      setInterimTranscript('');
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = '';
      let interim = '';
      let totalConfidence = 0;
      let confidenceCount = 0;

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const transcript = result[0].transcript;
        
        if (result.isFinal) {
          finalTranscript += transcript;
          totalConfidence += result[0].confidence;
          confidenceCount++;
        } else {
          interim += transcript;
        }
      }

      if (finalTranscript) {
        setInputText(prev => (prev + ' ' + finalTranscript).trim());
        setExtractedText(prev => (prev + ' ' + finalTranscript).trim());
        
        // Calculate ASR confidence
        const avgConfidence = confidenceCount > 0 ? totalConfidence / confidenceCount : 0.75;
        setConfidence(avgConfidence);
        setConfidenceType('ASR');
      }
      
      setInterimTranscript(interim);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      isRecognitionActiveRef.current = false;
      setIsRecording(false);
      
      switch (event.error) {
        case 'no-speech':
          setSpeechError('No speech detected. Please try again.');
          break;
        case 'audio-capture':
          setSpeechError('No microphone found. Please check your audio settings.');
          break;
        case 'not-allowed':
          setSpeechError('Microphone access denied. Please allow microphone access.');
          break;
        default:
          setSpeechError(`Error: ${event.error}. Please try again.`);
      }
    };

    recognition.onend = () => {
      isRecognitionActiveRef.current = false;
      setIsRecording(false);
      setInterimTranscript('');
      setIsEditing(true);
    };

    return recognition;
  }, []);

  const startRecording = useCallback(() => {
    setSpeechError(null);
    setInterimTranscript('');
    
    if (!recognitionRef.current) {
      recognitionRef.current = initSpeechRecognition();
    }

    if (recognitionRef.current && !isRecognitionActiveRef.current) {
      try {
        recognitionRef.current.start();
      } catch (error) {
        console.error('Failed to start recognition:', error);
        // Reinitialize if there's an error
        recognitionRef.current = initSpeechRecognition();
        if (recognitionRef.current) {
          recognitionRef.current.start();
        }
      }
    }
  }, [initSpeechRecognition]);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current && isRecognitionActiveRef.current) {
      recognitionRef.current.stop();
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

  const handleSubmit = () => {
    const finalText = inputText.trim();
    if (!finalText) return;

    const requiresHITL = confidence < 0.75;
    onSubmit({
      text: finalText,
      inputMode,
      confidence,
      requiresHITL,
    });
  };

  const currentText = inputText || extractedText;
  const requiresHITL = confidence < 0.75 && (inputMode === 'image' || inputMode === 'voice');

  return (
    <div className="space-y-6">
      {/* Input Mode Selector */}
      <div className="flex gap-2">
        {inputModes.map(({ mode, icon: Icon, label }) => (
          <Button
            key={mode}
            variant={inputMode === mode ? 'default' : 'glass'}
            size="sm"
            onClick={() => {
              setInputMode(mode);
              setUploadedImage(null);
              setExtractedText('');
              setInputText('');
              setConfidence(1);
              setConfidenceType(null);
              setSpeechError(null);
              setInterimTranscript('');
            }}
            className="flex-1"
          >
            <Icon className="w-4 h-4" />
            {label}
          </Button>
        ))}
      </div>

      {/* Text Input Mode */}
      <AnimatePresence mode="wait">
        {inputMode === 'text' && (
          <motion.div
            key="text"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4"
          >
            <div className="relative">
              <Textarea
                placeholder="Type your math question... (supports LaTeX: \int, \frac, \sqrt)"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                className="min-h-[120px] resize-none bg-card/50 border-border focus:border-primary"
              />
              {inputText && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute top-2 right-2"
                  onClick={() => setShowPreview(!showPreview)}
                >
                  <Eye className="w-4 h-4" />
                </Button>
              )}
            </div>
            
            {showPreview && inputText && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="p-4 bg-muted/50 rounded-lg"
              >
                <p className="text-xs text-muted-foreground mb-2">Preview</p>
                <KaTeXRenderer latex={inputText} displayMode />
              </motion.div>
            )}
          </motion.div>
        )}

        {/* Image Input Mode */}
        {inputMode === 'image' && (
          <motion.div
            key="image"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              className="hidden"
            />
            
            {!uploadedImage ? (
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full h-40 border-2 border-dashed border-border rounded-xl flex flex-col items-center justify-center gap-3 hover:border-primary hover:bg-primary/5 transition-colors"
              >
                <Upload className="w-8 h-8 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  Click to upload an image with math
                </span>
              </button>
            ) : (
              <div className="space-y-4">
                <div className="relative rounded-lg overflow-hidden">
                  <img
                    src={uploadedImage}
                    alt="Uploaded math"
                    className="w-full h-40 object-contain bg-muted"
                  />
                  <Button
                    variant="destructive"
                    size="icon"
                    className="absolute top-2 right-2"
                    onClick={() => {
                      setUploadedImage(null);
                      setExtractedText('');
                      setInputText('');
                      setConfidence(1);
                    }}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>

                {isExtracting ? (
                  <div className="flex items-center justify-center gap-2 p-4 bg-muted/50 rounded-lg">
                    <Loader2 className="w-5 h-5 animate-spin text-primary" />
                    <span className="text-sm">Extracting text with OCR...</span>
                  </div>
                ) : extractedText && (
                  <div className="space-y-3">
                    <ConfidenceMeter score={confidence} type={confidenceType} />
                    
                    <div className="p-4 bg-muted/50 rounded-lg space-y-3">
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-medium text-muted-foreground">
                          Extracted Text
                        </p>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setIsEditing(!isEditing)}
                        >
                          <Edit3 className="w-3 h-3 mr-1" />
                          {isEditing ? 'Done' : 'Edit'}
                        </Button>
                      </div>
                      
                      {isEditing ? (
                        <Textarea
                          value={inputText}
                          onChange={(e) => setInputText(e.target.value)}
                          className="bg-background/50"
                          rows={3}
                        />
                      ) : (
                        <p className="text-sm">{inputText}</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}

        {/* Voice Input Mode */}
        {inputMode === 'voice' && (
          <motion.div
            key="voice"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4"
          >
            {/* Speech Error */}
            {speechError && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 bg-destructive/10 border border-destructive/30 rounded-lg flex items-center gap-2"
              >
                <AlertCircle className="w-4 h-4 text-destructive flex-shrink-0" />
                <p className="text-sm text-destructive">{speechError}</p>
              </motion.div>
            )}

            <div className="flex flex-col items-center justify-center py-6 gap-4">
              <motion.button
                onClick={isRecording ? stopRecording : startRecording}
                className={`w-20 h-20 rounded-full flex items-center justify-center transition-colors relative ${
                  isRecording 
                    ? 'bg-destructive text-destructive-foreground' 
                    : 'bg-primary text-primary-foreground'
                }`}
                whileTap={{ scale: 0.95 }}
              >
                {isRecording && (
                  <motion.div
                    className="absolute inset-0 rounded-full border-4 border-destructive"
                    animate={{ scale: [1, 1.3, 1], opacity: [1, 0, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  />
                )}
                {isRecording ? (
                  <MicOff className="w-8 h-8" />
                ) : (
                  <Mic className="w-8 h-8" />
                )}
              </motion.button>
              
              {isRecording && (
                <motion.div
                  className="flex items-center gap-2"
                  animate={{ opacity: [1, 0.5, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                >
                  <span className="w-2 h-2 bg-destructive rounded-full" />
                  <span className="text-sm text-destructive font-medium">Listening...</span>
                </motion.div>
              )}
              
              <p className="text-sm text-muted-foreground text-center">
                {isRecording ? 'Speak now... Click to stop' : 'Click to start voice input'}
              </p>
            </div>

            {/* Live Transcript Preview (while recording) */}
            {isRecording && (inputText || interimTranscript) && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 bg-primary/5 border border-primary/20 rounded-lg space-y-2"
              >
                <p className="text-xs font-medium text-primary">Live Transcript</p>
                <p className="text-sm">
                  {inputText}
                  {interimTranscript && (
                    <span className="text-muted-foreground italic"> {interimTranscript}</span>
                  )}
                </p>
              </motion.div>
            )}

            {/* Final Transcript (after recording) */}
            {extractedText && !isRecording && (
              <div className="space-y-3">
                <ConfidenceMeter score={confidence} type={confidenceType} />
                
                <div className="p-4 bg-muted/50 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-medium text-muted-foreground">
                      Transcript (Edit if needed)
                    </p>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setIsEditing(!isEditing)}
                    >
                      <Edit3 className="w-3 h-3 mr-1" />
                      {isEditing ? 'Done' : 'Edit'}
                    </Button>
                  </div>
                  
                  {isEditing ? (
                    <Textarea
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      className="bg-background/50"
                      rows={3}
                      placeholder="Edit your transcript here..."
                    />
                  ) : (
                    <p className="text-sm">{inputText}</p>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* HITL Warning */}
      {requiresHITL && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-warning/10 border border-warning/30 rounded-lg"
        >
          <p className="text-sm font-medium text-warning">
            ⚠️ Low confidence detected. Please review and correct the extracted text before submitting.
          </p>
        </motion.div>
      )}

      {/* Submit Button */}
      <Button
        variant="hero"
        size="lg"
        className="w-full"
        onClick={handleSubmit}
        disabled={!currentText || isProcessing}
      >
        {isProcessing ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Processing...
          </>
        ) : (
          'Solve with AI Agents'
        )}
      </Button>
    </div>
  );
};

export default InputPanel;
