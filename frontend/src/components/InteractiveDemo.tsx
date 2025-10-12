'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Search, Sparkles, CheckCircle } from 'lucide-react';

const steps = [
  {
    id: 1,
    icon: Upload,
    title: 'Upload Document',
    description: 'Drop your PDF, DOCX, or TXT file',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    id: 2,
    icon: Sparkles,
    title: 'AI Processing',
    description: 'Converting to vector embeddings',
    color: 'from-purple-500 to-pink-500',
  },
  {
    id: 3,
    icon: Search,
    title: 'Query Ready',
    description: 'Ask questions in natural language',
    color: 'from-emerald-500 to-teal-500',
  },
  {
    id: 4,
    icon: CheckCircle,
    title: 'Get Answers',
    description: 'Receive accurate AI-powered responses',
    color: 'from-orange-500 to-red-500',
  },
];

export default function InteractiveDemo() {
  const [activeStep, setActiveStep] = useState(0);

  return (
    <div className="relative">
      <div className="flex justify-center mb-16">
        <div className="flex items-center space-x-6">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <motion.button
                onClick={() => setActiveStep(index)}
                className={`relative w-20 h-20 rounded-full flex items-center justify-center transition-all duration-500 shadow-lg ${
                  activeStep === index
                    ? 'bg-gradient-to-br ' + step.color + ' scale-110 shadow-xl shadow-blue-500/30'
                    : 'bg-gray-800 hover:bg-gray-700 border border-white/10'
                }`}
                whileHover={{ scale: 1.15 }}
                whileTap={{ scale: 0.95 }}
              >
                <step.icon className="w-10 h-10 text-white drop-shadow-sm" />
                {activeStep === index && (
                  <motion.div
                    layoutId="activeIndicator"
                    className="absolute inset-0 rounded-full border-4 border-white/40"
                    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                  />
                )}
              </motion.button>
              {index < steps.length - 1 && (
                <div className="w-16 h-2 bg-gray-800 mx-4 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full bg-gradient-to-r ${step.color} rounded-full`}
                    initial={{ width: 0 }}
                    animate={{ width: activeStep > index ? '100%' : '0%' }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={activeStep}
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -30 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="text-center"
        >
          <h3 className="text-4xl lg:text-5xl font-bold text-white mb-6 drop-shadow-lg">
            {steps[activeStep].title}
          </h3>
          <p className="text-xl lg:text-2xl text-gray-200 mb-12 font-light leading-relaxed">
            {steps[activeStep].description}
          </p>
          <div className={`w-full h-96 rounded-3xl bg-gradient-to-br ${steps[activeStep].color} opacity-25 flex items-center justify-center relative overflow-hidden group shadow-2xl border border-white/10`}>
            <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" />
            <div className={`absolute inset-0 bg-gradient-to-br ${steps[activeStep].color} opacity-0 group-hover:opacity-25 transition-opacity duration-700`} />
            {(() => {
              const IconComponent = steps[activeStep].icon;
              return <IconComponent className="w-48 h-48 text-white opacity-80 relative z-10 group-hover:scale-110 transition-all duration-700 drop-shadow-2xl" />;
            })()}
          </div>
        </motion.div>
      </AnimatePresence>

      <div className="flex justify-center mt-12 space-x-3">
        {steps.map((_, index) => (
          <motion.button
            key={index}
            onClick={() => setActiveStep(index)}
            className={`h-4 rounded-full transition-all duration-500 ${
              activeStep === index ? 'bg-gradient-to-r from-blue-500 to-cyan-500 w-12 shadow-lg shadow-cyan-500/30' : 'bg-gray-600 w-4 hover:bg-gray-500'
            }`}
            whileHover={{ scale: 1.2 }}
            whileTap={{ scale: 0.9 }}
          />
        ))}
      </div>
    </div>
  );
}