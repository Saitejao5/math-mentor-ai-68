import React, { useEffect, useRef } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

interface KaTeXRendererProps {
  latex: string;
  displayMode?: boolean;
  className?: string;
}

const KaTeXRenderer: React.FC<KaTeXRendererProps> = ({ 
  latex, 
  displayMode = false,
  className = ''
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current && latex) {
      try {
        katex.render(latex, containerRef.current, {
          displayMode,
          throwOnError: false,
          errorColor: '#ef4444',
          trust: true,
          strict: false,
        });
      } catch (error) {
        console.error('KaTeX rendering error:', error);
        if (containerRef.current) {
          containerRef.current.textContent = latex;
        }
      }
    }
  }, [latex, displayMode]);

  return (
    <div 
      ref={containerRef} 
      className={`katex-container ${className}`}
    />
  );
};

export default KaTeXRenderer;
