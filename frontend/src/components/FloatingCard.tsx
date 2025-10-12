'use client';

import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface FloatingCardProps {
  children: ReactNode;
  delay?: number;
  className?: string;
}

export default function FloatingCard({ children, delay = 0, className = '' }: FloatingCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 60 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.8, delay, ease: "easeOut" }}
      whileHover={{
        y: -12,
        scale: 1.03,
        transition: { duration: 0.4, ease: "easeOut" }
      }}
      className={`glass-strong rounded-3xl p-8 border border-white/15 hover:border-white/25 hover:shadow-2xl hover:shadow-blue-500/30 transition-all duration-500 backdrop-blur-xl ${className}`}
    >
      {children}
    </motion.div>
  );
}