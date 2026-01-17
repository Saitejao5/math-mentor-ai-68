import React, { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, GraduationCap, Sparkles, Settings } from 'lucide-react';
import { Button } from './ui/button';
import { useNavigate } from 'react-router-dom';
import InputPanel from './InputPanel';
import AgentTimeline, { Agent } from './AgentTimeline';
import ResultPanel from './ResultPanel';
import ConfidenceMeter from './ConfidenceMeter';

const initialAgents: Agent[] = [
  { name: 'parser', displayName: 'Parser Agent', description: 'Understanding and normalizing question', status: 'pending' },
  { name: 'router', displayName: 'Router Agent', description: 'Deciding solving strategy', status: 'pending' },
  { name: 'solver', displayName: 'Solver Agent', description: 'Solving mathematically', status: 'pending' },
  { name: 'verifier', displayName: 'Verifier Agent', description: 'Checking correctness', status: 'pending' },
  { name: 'explainer', displayName: 'Explainer Agent', description: 'Creating step-by-step explanation', status: 'pending' },
];

const TutorInterface: React.FC = () => {
  const navigate = useNavigate();
  const [isProcessing, setIsProcessing] = useState(false);
  const [agents, setAgents] = useState<Agent[]>(initialAgents);
  const [currentQuestion, setCurrentQuestion] = useState<string>('');
  const [inputConfidence, setInputConfidence] = useState<number>(1);
  const [result, setResult] = useState<any>(null);

  const simulateAgentProcessing = useCallback(async (questionData: {
    text: string;
    inputMode: string;
    confidence: number;
    requiresHITL: boolean;
  }) => {
    try {
      console.log('Sending request to backend:', questionData);
      
      // FIXED: Changed endpoint from root to /api/solve
      const response = await fetch('https://math-mentor-ai-68-4.onrender.com/api/solve', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(questionData)
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API error response:', errorText);
        throw new Error(`API error: ${response.status} - ${errorText}`);
      }

      const backendResult = await response.json();
      console.log('Received backend result:', backendResult);

      // Animate through agents using backend results
      if (backendResult.agentResults && backendResult.agentResults.length > 0) {
        for (let i = 0; i < backendResult.agentResults.length; i++) {
          const agentResult = backendResult.agentResults[i];
          
          // Update agent status to running
          setAgents(prev => prev.map((agent, idx) => ({
            ...agent,
            status: idx === i ? 'running' : idx < i ? 'completed' : 'pending',
            result: idx < i ? backendResult.agentResults[idx].result : undefined,
          })));
          
          // Wait before moving to next agent
          await new Promise(resolve => setTimeout(resolve, 800));
        }

        // Mark all agents as completed
        setAgents(prev => prev.map((agent, idx) => ({
          ...agent,
          status: 'completed',
          result: backendResult.agentResults[idx]?.result || 'Completed',
        })));
      } else {
        // Fallback: animate through agents without specific results
        const agentNames = ['parser', 'router', 'solver', 'verifier', 'explainer'];
        for (let i = 0; i < agentNames.length; i++) {
          setAgents(prev => prev.map((agent, idx) => ({
            ...agent,
            status: idx === i ? 'running' : idx < i ? 'completed' : 'pending',
          })));
          await new Promise(resolve => setTimeout(resolve, 600));
        }

        // Mark all as completed
        setAgents(prev => prev.map(agent => ({
          ...agent,
          status: 'completed',
        })));
      }

      // Set the result from backend
      console.log('Setting result state:', backendResult);
      setResult(backendResult);
      setIsProcessing(false);

    } catch (error) {
      console.error('Error processing question:', error);
      
      // Show error state in agents
      setAgents(prev => prev.map(agent => ({
        ...agent,
        status: 'completed',
        result: 'Error occurred',
      })));

      // Set error result
      setResult({
        finalAnswer: {
          latex: 'Error processing question. Please try again.',
          confidence: 0,
        },
        steps: [
          {
            step: 1,
            description: 'An error occurred while processing your question',
            latex: error instanceof Error ? error.message : 'Unknown error',
          },
        ],
        verification: {
          status: 'failed',
          method: 'error',
        },
        agentTrace: ['parser', 'router', 'solver', 'verifier', 'explainer'],
        hitlApplied: false,
      });

      setIsProcessing(false);
    }
  }, []);

  const handleSubmit = useCallback((data: {
    text: string;
    inputMode: string;
    confidence: number;
    requiresHITL: boolean;
  }) => {
    console.log('Question submitted:', data);
    setCurrentQuestion(data.text);
    setInputConfidence(data.confidence);
    setIsProcessing(true);
    setResult(null);
    setAgents(initialAgents);
    
    // Pass the full data object to the processing function
    simulateAgentProcessing(data);
  }, [simulateAgentProcessing]);

  const resetSession = () => {
    setIsProcessing(false);
    setAgents(initialAgents);
    setCurrentQuestion('');
    setInputConfidence(1);
    setResult(null);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-background/80 border-b border-border">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              size="icon"
              onClick={() => navigate('/')}
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-[hsl(258,89%,60%)] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="font-bold font-display">Math Mentor AI</h1>
                <p className="text-xs text-muted-foreground">JEE Problem Solver</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-accent/10 rounded-full">
              <GraduationCap className="w-4 h-4 text-accent" />
              <span className="text-sm font-medium text-accent">JEE Mode</span>
            </div>
            
            {isProcessing && (
              <div className="hidden md:block w-32">
                <ConfidenceMeter score={inputConfidence} showLabel={false} size="sm" />
              </div>
            )}

            <Button variant="ghost" size="icon">
              <Settings className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Panel - Input */}
          <div className="space-y-6">
            <div className="glass-card rounded-2xl p-6">
              <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  1
                </span>
                Enter Your Question
              </h2>
              <InputPanel onSubmit={handleSubmit} isProcessing={isProcessing} />
            </div>

            {/* Agent Timeline */}
            <AnimatePresence>
              {(isProcessing || result) && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="glass-card rounded-2xl p-6"
                >
                  <AgentTimeline agents={agents} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Right Panel - Result */}
          <div className="glass-card rounded-2xl p-6 min-h-[500px]">
            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <span className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                2
              </span>
              Solution
            </h2>
            <ResultPanel result={result} isLoading={isProcessing} />
          </div>
        </div>

        {/* Current Question Display */}
        {currentQuestion && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 p-4 glass-card rounded-xl"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Current Question</p>
                <p className="font-medium">{currentQuestion}</p>
              </div>
              <Button variant="outline" size="sm" onClick={resetSession}>
                New Question
              </Button>
            </div>
          </motion.div>
        )}
      </main>
    </div>
  );
};

export default TutorInterface;
