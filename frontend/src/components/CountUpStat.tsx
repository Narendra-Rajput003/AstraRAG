'use client';

import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

interface CountUpStatProps {
  end: number;
  duration?: number;
  suffix?: string;
  prefix?: string;
  label: string;
  description?: string;
  decimals?: number;
}

export default function CountUpStat({
  end,
  duration = 2,
  suffix = '',
  prefix = '',
  label,
  description,
  decimals = 0,
}: CountUpStatProps) {
  const [count, setCount] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isVisible) {
          setIsVisible(true);
        }
      },
      { threshold: 0.3 }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current);
      }
    };
  }, [isVisible]);

  useEffect(() => {
    if (!isVisible) return;

    let startTime: number | null = null;
    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime;
      const progress = Math.min((currentTime - startTime) / (duration * 1000), 1);

      setCount(progress * end);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [isVisible, end, duration]);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, scale: 0.8, y: 30 }}
      whileInView={{ opacity: 1, scale: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.7, ease: "easeOut" }}
      className="text-center group"
    >
      <div className="text-5xl md:text-6xl lg:text-7xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-3 drop-shadow-lg group-hover:scale-105 transition-transform duration-500">
        {prefix}
        {count.toFixed(decimals)}
        {suffix}
      </div>
      <div className="text-gray-200 font-semibold text-xl lg:text-2xl mb-2">{label}</div>
      {description && <div className="text-gray-400 text-base lg:text-lg font-light">{description}</div>}
    </motion.div>
  );
}