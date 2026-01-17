import React from 'react';
import { motion } from 'framer-motion';
import { Shield, ShieldCheck, ShieldAlert } from 'lucide-react';

interface ConfidenceMeterProps {
  score: number;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({ 
  score, 
  showLabel = true,
  size = 'md'
}) => {
  const percentage = Math.round(score * 100);
  
  const getStatus = () => {
    if (percentage >= 85) return { label: 'High Confidence', color: 'text-success', bgColor: 'bg-success', Icon: ShieldCheck };
    if (percentage >= 75) return { label: 'Good Confidence', color: 'text-accent', bgColor: 'bg-accent', Icon: Shield };
    return { label: 'Low Confidence', color: 'text-destructive', bgColor: 'bg-destructive', Icon: ShieldAlert };
  };

  const status = getStatus();
  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3'
  };

  return (
    <div className="flex flex-col gap-2">
      {showLabel && (
        <div className="flex items-center justify-between">
          <div className={`flex items-center gap-1.5 ${status.color}`}>
            <status.Icon className="w-4 h-4" />
            <span className="text-sm font-medium">{status.label}</span>
          </div>
          <span className={`text-sm font-bold ${status.color}`}>{percentage}%</span>
        </div>
      )}
      <div className={`w-full ${sizeClasses[size]} bg-muted rounded-full overflow-hidden`}>
        <motion.div
          className={`h-full ${status.bgColor} rounded-full`}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
};

export default ConfidenceMeter;
