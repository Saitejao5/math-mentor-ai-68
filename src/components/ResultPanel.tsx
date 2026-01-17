import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, Copy, Download, Check, ShieldCheck, Users } from 'lucide-react';
import { Button } from './ui/button';
import KaTeXRenderer from './KaTeXRenderer';
import ConfidenceMeter from './ConfidenceMeter';

interface Step {
  step: number;
  description: string;
  latex: string;
}

interface ResultData {
  finalAnswer: {
    latex: string;
    confidence: number;
  };
  steps: Step[];
  verification: {
    status: string;
    method: string;
  };
  agentTrace: string[];
  hitlApplied?: boolean;
}

interface ResultPanelProps {
  result: ResultData | null;
  isLoading: boolean;
}

const ResultPanel: React.FC<ResultPanelProps> = ({ result, isLoading }) => {
  const [expandedSteps, setExpandedSteps] = useState<number[]>([]);
  const [copied, setCopied] = useState(false);

  const toggleStep = (stepNum: number) => {
    setExpandedSteps(prev => 
      prev.includes(stepNum) 
        ? prev.filter(s => s !== stepNum)
        : [...prev, stepNum]
    );
  };

  const copyLatex = async () => {
    if (result?.finalAnswer.latex) {
      await navigator.clipboard.writeText(result.finalAnswer.latex);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
            <motion.div
              className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full"
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            />
          </div>
          <p className="text-muted-foreground">Agents are working...</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center space-y-4 max-w-xs">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto">
            <span className="text-2xl">🧠</span>
          </div>
          <div>
            <h3 className="font-semibold text-foreground">Ready to Solve</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Enter a math problem and our AI agents will solve it step by step.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Trust Badges */}
      <div className="flex flex-wrap gap-2">
        {result.verification.status === 'verified' && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-success/10 text-success rounded-full text-sm font-medium">
            <ShieldCheck className="w-4 h-4" />
            Verified
          </div>
        )}
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-sm font-medium">
          <Users className="w-4 h-4" />
          5 AI Agents
        </div>
        {result.hitlApplied && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-accent/10 text-accent rounded-full text-sm font-medium">
            👨‍🏫 Human Verified
          </div>
        )}
      </div>

      {/* Final Answer */}
      <div className="p-6 glass-card rounded-xl space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-lg">Final Answer</h3>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={copyLatex}>
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </Button>
            <Button variant="ghost" size="sm">
              <Download className="w-4 h-4" />
            </Button>
          </div>
        </div>
        
        <div className="p-4 bg-muted/30 rounded-lg overflow-x-auto">
          <KaTeXRenderer latex={result.finalAnswer.latex} displayMode />
        </div>

        <ConfidenceMeter score={result.finalAnswer.confidence} />
      </div>

      {/* Step by Step */}
      <div className="space-y-3">
        <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">
          Step-by-Step Solution
        </h3>
        
        <div className="space-y-2">
          {result.steps.map((step) => (
            <motion.div
              key={step.step}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: step.step * 0.1 }}
              className="glass-card rounded-lg overflow-hidden"
            >
              <button
                onClick={() => toggleStep(step.step)}
                className="w-full p-4 flex items-center justify-between text-left hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="w-7 h-7 rounded-full bg-primary/10 text-primary text-sm font-bold flex items-center justify-center">
                    {step.step}
                  </span>
                  <span className="font-medium">{step.description}</span>
                </div>
                {expandedSteps.includes(step.step) ? (
                  <ChevronUp className="w-5 h-5 text-muted-foreground" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-muted-foreground" />
                )}
              </button>
              
              <AnimatePresence>
                {expandedSteps.includes(step.step) && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="border-t border-border"
                  >
                    <div className="p-4 bg-muted/20">
                      <KaTeXRenderer latex={step.latex} displayMode />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Verification Method */}
      <div className="p-4 bg-success/5 border border-success/20 rounded-lg">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-success" />
          <span className="font-medium text-success">
            Verified via {result.verification.method}
          </span>
        </div>
      </div>
    </motion.div>
  );
};

export default ResultPanel;
