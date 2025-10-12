import React from 'react';

const HeroIllustration: React.FC = () => {
  return (
    <div className="relative w-full h-96 md:h-[500px] lg:h-[600px]">
      <svg
        viewBox="0 0 800 600"
        className="w-full h-full"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Background gradient */}
        <defs>
          <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#1a1a2e" />
            <stop offset="50%" stopColor="#16213e" />
            <stop offset="100%" stopColor="#0f3460" />
          </linearGradient>
          <linearGradient id="aiGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#667eea" />
            <stop offset="50%" stopColor="#764ba2" />
            <stop offset="100%" stopColor="#f093fb" />
          </linearGradient>
          <radialGradient id="glowGradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#667eea" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#667eea" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Background */}
        <rect width="800" height="600" fill="url(#bgGradient)" />

        {/* Neural network nodes */}
        <g className="animate-pulse">
          {/* Central AI brain */}
          <circle cx="400" cy="300" r="80" fill="url(#aiGradient)" opacity="0.8" />
          <circle cx="400" cy="300" r="60" fill="none" stroke="#667eea" strokeWidth="2" opacity="0.6" />

          {/* Surrounding nodes */}
          <circle cx="250" cy="200" r="25" fill="#764ba2" opacity="0.7" />
          <circle cx="550" cy="200" r="25" fill="#764ba2" opacity="0.7" />
          <circle cx="200" cy="350" r="20" fill="#f093fb" opacity="0.6" />
          <circle cx="600" cy="350" r="20" fill="#f093fb" opacity="0.6" />
          <circle cx="320" cy="450" r="18" fill="#667eea" opacity="0.5" />
          <circle cx="480" cy="450" r="18" fill="#667eea" opacity="0.5" />

          {/* Connection lines */}
          <line x1="320" y1="225" x2="400" y2="240" stroke="#667eea" strokeWidth="2" opacity="0.4" />
          <line x1="480" y1="225" x2="400" y2="240" stroke="#667eea" strokeWidth="2" opacity="0.4" />
          <line x1="280" y1="350" x2="400" y2="360" stroke="#764ba2" strokeWidth="2" opacity="0.4" />
          <line x1="520" y1="350" x2="400" y2="360" stroke="#764ba2" strokeWidth="2" opacity="0.4" />
          <line x1="338" y1="432" x2="400" y2="380" stroke="#f093fb" strokeWidth="2" opacity="0.4" />
          <line x1="462" y1="432" x2="400" y2="380" stroke="#f093fb" strokeWidth="2" opacity="0.4" />
        </g>

        {/* Data flow particles */}
        <g className="animate-float">
          <circle cx="300" cy="150" r="3" fill="#667eea" opacity="0.8" />
          <circle cx="500" cy="150" r="3" fill="#764ba2" opacity="0.8" />
          <circle cx="150" cy="400" r="2" fill="#f093fb" opacity="0.6" />
          <circle cx="650" cy="400" r="2" fill="#f093fb" opacity="0.6" />
        </g>

        {/* Glow effect */}
        <circle cx="400" cy="300" r="150" fill="url(#glowGradient)" opacity="0.3" />
      </svg>
    </div>
  );
};

export default HeroIllustration;