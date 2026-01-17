import React from 'react';
import { motion } from 'framer-motion';
import { Check, Loader2, Circle, FileSearch, Route, Calculator, CheckCircle2, BookOpen } from 'lucide-react';

export type AgentStatus = 'pending' | 'running' | 'completed' | 'error';

export interface Agent {
  name: string;
  displayName: string;
  description: string;
  status: AgentStatus;
  result?: string;
}

interface AgentTimelineProps {
  agents: Agent[];
}

const agentIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  parser: FileSearch,
  router: Route,
  solver: Calculator,
  verifier: CheckCircle2,
  explainer: BookOpen,
};

const agentColors: Record<string, string> = {
  parser: 'bg-agent-parser',
  router: 'bg-agent-router',
  solver: 'bg-agent-solver',
  verifier: 'bg-agent-verifier',
  explainer: 'bg-agent-explainer',
};

const AgentTimeline: React.FC<AgentTimelineProps> = ({ agents }) => {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
        Agent Pipeline
      </h3>
      <div className="space-y-3">
        {agents.map((agent, index) => {
          const Icon = agentIcons[agent.name] || Circle;
          const bgColor = agentColors[agent.name] || 'bg-primary';
          
          return (
            <motion.div
              key={agent.name}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`flex items-start gap-3 p-3 rounded-lg transition-colors ${
                agent.status === 'running' 
                  ? 'bg-primary/5 border border-primary/20' 
                  : agent.status === 'completed'
                  ? 'bg-success/5 border border-success/20'
                  : 'bg-muted/50'
              }`}
            >
              {/* Status indicator */}
              <div className="relative flex-shrink-0">
                <div className={`w-10 h-10 rounded-lg ${bgColor} flex items-center justify-center`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                {agent.status === 'running' && (
                  <motion.div
                    className={`absolute inset-0 rounded-lg ${bgColor}/30`}
                    animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  />
                )}
              </div>
              
              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-foreground">{agent.displayName}</span>
                  {agent.status === 'completed' && (
                    <Check className="w-4 h-4 text-success" />
                  )}
                  {agent.status === 'running' && (
                    <Loader2 className="w-4 h-4 text-primary animate-spin" />
                  )}
                </div>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {agent.status === 'completed' && agent.result 
                    ? agent.result 
                    : agent.description
                  }
                </p>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default AgentTimeline;
