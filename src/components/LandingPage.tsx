import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Zap, GraduationCap, ArrowRight, Play, ChevronRight } from 'lucide-react';
import { Button } from './ui/button';
import { useNavigate } from 'react-router-dom';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [isHovering, setIsHovering] = useState(false);

  const features = [
    {
      icon: Brain,
      title: 'Multi-Agent AI',
      description: '5 specialized AI agents work together to solve and verify your math problems',
    },
    {
      icon: Zap,
      title: 'Instant Solutions',
      description: 'Get step-by-step explanations with beautiful LaTeX rendering in seconds',
    },
    {
      icon: GraduationCap,
      title: 'JEE & Advanced',
      description: 'Optimized for competitive exam patterns including JEE Main & Advanced',
    },
  ];

  const agentDemo = [
    { name: 'Parser', status: 'done', delay: 0 },
    { name: 'Router', status: 'done', delay: 0.3 },
    { name: 'Solver', status: 'active', delay: 0.6 },
    { name: 'Verifier', status: 'pending', delay: 0.9 },
    { name: 'Explainer', status: 'pending', delay: 1.2 },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 hero-pattern" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/50 to-background" />
        
        {/* Floating Orbs */}
        <motion.div
          className="absolute top-20 left-10 w-72 h-72 bg-primary/10 rounded-full blur-3xl"
          animate={{ x: [0, 30, 0], y: [0, -20, 0] }}
          transition={{ duration: 8, repeat: Infinity }}
        />
        <motion.div
          className="absolute bottom-20 right-10 w-96 h-96 bg-accent/10 rounded-full blur-3xl"
          animate={{ x: [0, -20, 0], y: [0, 30, 0] }}
          transition={{ duration: 10, repeat: Infinity }}
        />

        <div className="relative container mx-auto px-4 py-20 lg:py-32">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Text Content */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="space-y-8"
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full text-primary text-sm font-medium">
                <Zap className="w-4 h-4" />
                Powered by 5 AI Agents
              </div>

              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold font-display leading-tight">
                Your Personal{' '}
                <span className="gradient-text">JEE Math Tutor</span>
              </h1>

              <p className="text-xl text-muted-foreground max-w-lg">
                Ask any math question via text, image, or voice. Our AI team solves it step-by-step, 
                verifies correctness, and explains concepts beautifully.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <Button 
                  variant="hero" 
                  size="xl"
                  onClick={() => navigate('/tutor')}
                  onMouseEnter={() => setIsHovering(true)}
                  onMouseLeave={() => setIsHovering(false)}
                >
                  Start Solving
                  <motion.div
                    animate={{ x: isHovering ? 5 : 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ArrowRight className="w-5 h-5" />
                  </motion.div>
                </Button>
                <Button variant="outline" size="xl">
                  <Play className="w-4 h-4" />
                  Watch Demo
                </Button>
              </div>

              <div className="flex items-center gap-8 pt-4">
                <div>
                  <p className="text-3xl font-bold gradient-text">50K+</p>
                  <p className="text-sm text-muted-foreground">Problems Solved</p>
                </div>
                <div className="w-px h-12 bg-border" />
                <div>
                  <p className="text-3xl font-bold gradient-text">98%</p>
                  <p className="text-sm text-muted-foreground">Accuracy Rate</p>
                </div>
                <div className="w-px h-12 bg-border" />
                <div>
                  <p className="text-3xl font-bold gradient-text">4.9★</p>
                  <p className="text-sm text-muted-foreground">User Rating</p>
                </div>
              </div>
            </motion.div>

            {/* Right: Agent Demo Animation */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="relative"
            >
              <div className="glass-card rounded-2xl p-6 lg:p-8">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">Agent Pipeline</span>
                    <span className="px-2 py-1 bg-success/10 text-success text-xs font-medium rounded-full">
                      Live
                    </span>
                  </div>

                  <div className="p-4 bg-muted/50 rounded-lg mb-4">
                    <p className="text-sm text-muted-foreground mb-2">Question:</p>
                    <p className="font-medium">Find ∫ x² eˣ dx</p>
                  </div>

                  <div className="space-y-3">
                    {agentDemo.map((agent, index) => (
                      <motion.div
                        key={agent.name}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: agent.delay + 0.5 }}
                        className={`flex items-center gap-3 p-3 rounded-lg ${
                          agent.status === 'active' 
                            ? 'bg-primary/10 border border-primary/20'
                            : agent.status === 'done'
                            ? 'bg-success/10'
                            : 'bg-muted/30'
                        }`}
                      >
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                          agent.status === 'done' 
                            ? 'bg-success text-success-foreground'
                            : agent.status === 'active'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted-foreground/20 text-muted-foreground'
                        }`}>
                          {agent.status === 'done' ? '✓' : agent.status === 'active' ? (
                            <motion.div
                              animate={{ rotate: 360 }}
                              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                              className="w-4 h-4 border-2 border-current border-t-transparent rounded-full"
                            />
                          ) : (index + 1)}
                        </div>
                        <span className={`font-medium ${
                          agent.status === 'pending' ? 'text-muted-foreground' : ''
                        }`}>
                          {agent.name} Agent
                        </span>
                        {agent.status === 'active' && (
                          <span className="ml-auto text-xs text-primary animate-pulse">
                            Processing...
                          </span>
                        )}
                      </motion.div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Decorative elements */}
              <div className="absolute -z-10 -top-4 -right-4 w-full h-full bg-gradient-to-br from-primary/20 to-accent/20 rounded-2xl blur-xl" />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-muted/30">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center max-w-2xl mx-auto mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold font-display mb-4">
              Why Choose Math Mentor AI?
            </h2>
            <p className="text-lg text-muted-foreground">
              Our multi-agent system ensures accuracy, clarity, and deep understanding
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="glass-card-hover p-8 rounded-2xl text-center"
              >
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-primary/50 flex items-center justify-center mx-auto mb-6">
                  <feature.icon className="w-8 h-8 text-primary-foreground" />
                </div>
                <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary via-primary to-[hsl(258,89%,50%)] p-12 md:p-16 text-center"
          >
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjEpIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-30" />
            
            <div className="relative z-10 max-w-2xl mx-auto space-y-6">
              <h2 className="text-3xl md:text-4xl font-bold font-display text-primary-foreground">
                Ready to Ace Your JEE Math?
              </h2>
              <p className="text-lg text-primary-foreground/80">
                Join thousands of students solving complex problems with confidence
              </p>
              <Button 
                variant="accent" 
                size="xl"
                onClick={() => navigate('/tutor')}
                className="mt-4"
              >
                Get Started Free
                <ChevronRight className="w-5 h-5" />
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-border">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>© 2025 Math Mentor AI. Built for JEE aspirants with ❤️</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
