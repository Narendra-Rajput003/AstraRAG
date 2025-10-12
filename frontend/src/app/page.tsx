'use client';

import { motion } from 'framer-motion';
import { ArrowRight, FileText, Search, Shield, Database, Zap, Brain, Sparkles, TrendingUp, Users, Clock, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';
import AnimatedBackground from '@/components/AnimatedBackground';
import FloatingCard from '@/components/FloatingCard';
import CountUpStat from '@/components/CountUpStat';
import InteractiveDemo from '@/components/InteractiveDemo';
import Footer from '@/components/Footer';

export default function Home() {
  const fadeInUp = {
    initial: { opacity: 0, y: 60 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 }
  };

  const stagger = {
    animate: {
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const features = [
    {
      icon: <FileText className="h-10 w-10" />,
      title: "Smart Document Processing",
      description: "Upload any format - PDF, DOCX, TXT. Our AI automatically chunks and processes your documents for optimal retrieval.",
      gradient: "from-blue-500 to-cyan-500",
      size: "large"
    },
    {
      icon: <Brain className="h-8 w-8" />,
      title: "Neural Search",
      description: "Advanced vector embeddings powered by state-of-the-art language models.",
      gradient: "from-purple-500 to-pink-500",
      size: "normal"
    },
    {
      icon: <Sparkles className="h-8 w-8" />,
      title: "Context-Aware AI",
      description: "Get precise answers with full context understanding and source attribution.",
      gradient: "from-emerald-500 to-teal-500",
      size: "normal"
    },
    {
      icon: <Shield className="h-8 w-8" />,
      title: "Enterprise Security",
      description: "JWT authentication, MFA support, and role-based access control.",
      gradient: "from-orange-500 to-red-500",
      size: "normal"
    },
    {
      icon: <Database className="h-8 w-8" />,
      title: "Scalable Architecture",
      description: "Built on FastAPI with vector databases for lightning-fast retrieval at any scale.",
      gradient: "from-indigo-500 to-purple-500",
      size: "normal"
    },
    {
      icon: <Zap className="h-8 w-8" />,
      title: "Real-time Processing",
      description: "Instant query responses with WebSocket support for live updates.",
      gradient: "from-yellow-500 to-orange-500",
      size: "normal"
    }
  ];

  const benefits = [
    { icon: <TrendingUp className="h-6 w-6" />, text: "10x faster document search" },
    { icon: <Users className="h-6 w-6" />, text: "Unlimited team members" },
    { icon: <Clock className="h-6 w-6" />, text: "24/7 AI availability" },
    { icon: <CheckCircle2 className="h-6 w-6" />, text: "99.9% uptime guarantee" },
  ];

  return (
    <div className="min-h-screen bg-black">
      {/* Hero Section with Aurora Background */}
      <section className="relative min-h-screen flex items-center overflow-hidden pt-20">
        {/* Animated Background */}
        <div className="absolute inset-0 bg-mesh">
          <AnimatedBackground />
        </div>

        {/* Aurora Effects - Enhanced with more layers and better positioning */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-aurora" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-aurora" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-aurora" style={{ animationDelay: '4s' }} />
        <div className="absolute top-1/3 right-1/3 w-64 h-64 bg-pink-500/15 rounded-full blur-2xl animate-aurora" style={{ animationDelay: '6s' }} />
        <div className="absolute bottom-1/3 left-1/3 w-80 h-80 bg-emerald-500/12 rounded-full blur-3xl animate-aurora" style={{ animationDelay: '8s' }} />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 z-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Left Column - Main Content Card */}
            <motion.div
              initial="initial"
              animate="animate"
              variants={stagger}
              className="space-y-8"
            >
              <FloatingCard delay={0.1} className="text-center lg:text-left">
                {/* Badge - Enhanced with better styling */}
                <motion.div
                  variants={fadeInUp}
                  className="inline-flex items-center space-x-2 bg-gradient-to-r from-white/5 to-white/10 backdrop-blur-md border border-white/20 rounded-full px-6 py-3 mb-6 shadow-lg shadow-cyan-500/10"
                >
                  <Sparkles className="h-5 w-5 text-cyan-400 animate-pulse" />
                  <span className="text-gray-200 font-semibold text-sm">Powered by Advanced AI Technology</span>
                </motion.div>

                {/* Main Heading - Improved typography and spacing */}
                <motion.h1
                  className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 leading-[0.9] text-display tracking-tight"
                  variants={fadeInUp}
                >
                  <span className="text-white drop-shadow-lg">Transform</span>
                  <br />
                  <span className="gradient-text-cyan drop-shadow-lg">Documents</span>
                  <br />
                  <span className="text-white drop-shadow-lg">Into</span>{' '}
                  <span className="gradient-text drop-shadow-lg">Intelligence</span>
                </motion.h1>

                <motion.p
                  className="text-lg lg:text-xl text-gray-200 mb-8 leading-relaxed font-light"
                  variants={fadeInUp}
                >
                  Experience the future of knowledge retrieval with our AI-powered RAG system.
                  Upload, query, and get instant intelligent answers from your documents.
                </motion.p>

                {/* CTA Buttons - Enhanced with better styling and spacing */}
                <motion.div
                  className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start"
                  variants={fadeInUp}
                >
                  <Link href="/login">
                    <motion.button
                      className="px-8 py-4 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 text-white rounded-2xl font-bold text-lg shadow-2xl hover:shadow-blue-500/60 transition-all duration-500 flex items-center gap-3 glow-cyan animate-gradient border border-white/20"
                      whileHover={{ scale: 1.05, y: -2 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      Start Free Trial
                      <ArrowRight className="h-5 w-5" />
                    </motion.button>
                  </Link>

                  <motion.button
                    className="px-8 py-4 glass-strong text-gray-100 rounded-2xl font-bold text-lg hover:bg-white/15 transition-all duration-500 border border-white/20 shadow-xl hover:shadow-white/10"
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    Watch Demo
                  </motion.button>
                </motion.div>
              </FloatingCard>

              {/* Benefits Row - Enhanced with better spacing and styling */}
              <motion.div
                variants={fadeInUp}
                className="grid grid-cols-2 gap-4"
              >
                {benefits.map((benefit, index) => (
                  <FloatingCard key={index} delay={0.3 + index * 0.1} className="p-4">
                    <div className="flex items-center space-x-3">
                      <div className="text-cyan-400 drop-shadow-sm">{benefit.icon}</div>
                      <span className="text-gray-200 text-sm font-semibold">{benefit.text}</span>
                    </div>
                  </FloatingCard>
                ))}
              </motion.div>
            </motion.div>

            {/* Right Column - Visual Element */}
            <motion.div
              initial={{ opacity: 0, x: 60 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="flex justify-center lg:justify-end"
            >
              <FloatingCard delay={0.6} className="w-full max-w-md">
                <div className="text-center p-8">
                  <div className="w-32 h-32 mx-auto mb-6 bg-gradient-to-br from-blue-500 to-purple-500 rounded-3xl flex items-center justify-center shadow-lg">
                    <FileText className="h-16 w-16 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-4">AI-Powered RAG</h3>
                  <p className="text-gray-300 text-sm leading-relaxed">
                    Transform your documents into intelligent knowledge bases with our advanced retrieval-augmented generation system.
                  </p>
                </div>
              </FloatingCard>
            </motion.div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <motion.div
          className="absolute bottom-10 left-1/2 transform -translate-x-1/2"
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div className="w-6 h-10 border-2 border-gray-600 rounded-full flex justify-center">
            <div className="w-1 h-3 bg-gray-400 rounded-full mt-2" />
          </div>
        </motion.div>
      </section>

      {/* Features Section - Bento Grid - Enhanced spacing and background */}
      <section className="py-24 bg-gradient-to-b from-black via-gray-900 to-black relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/15 via-transparent to-transparent" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center mb-20"
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            variants={stagger}
          >
            <FloatingCard delay={0.1} className="max-w-4xl mx-auto mb-16">
              <motion.h2
                className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 text-display leading-tight"
                variants={fadeInUp}
              >
                Everything You Need,{' '}
                <span className="gradient-text drop-shadow-lg">Nothing You Don't</span>
              </motion.h2>
              <motion.p
                className="text-lg lg:text-xl text-gray-300 font-light leading-relaxed"
                variants={fadeInUp}
              >
                Built for developers, designed for scale, loved by teams
              </motion.p>
            </FloatingCard>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <FloatingCard
                key={index}
                delay={index * 0.15}
                className={`${feature.size === 'large' ? 'md:col-span-2 lg:col-span-2' : ''} group cursor-pointer`}
              >
                <div className="flex flex-col h-full">
                  <div className={`p-4 bg-gradient-to-br ${feature.gradient} rounded-2xl mb-6 inline-block group-hover:scale-110 transition-all duration-500 shadow-lg group-hover:shadow-xl group-hover:shadow-blue-500/30 self-start`}>
                    <div className="text-white drop-shadow-sm">{feature.icon}</div>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl lg:text-2xl font-bold text-white mb-4 text-display leading-tight">{feature.title}</h3>
                    <p className="text-gray-300 leading-relaxed text-base">{feature.description}</p>
                  </div>
                </div>
              </FloatingCard>
            ))}
          </div>
        </div>
      </section>

      {/* Interactive Demo Section - Enhanced with better background and spacing */}
      <section className="py-24 bg-black relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/12 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/12 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
          <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-cyan-500/8 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
        </div>

        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center mb-16"
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            variants={stagger}
          >
            <FloatingCard delay={0.1} className="max-w-4xl mx-auto mb-12">
              <motion.h2
                className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 text-display leading-tight"
                variants={fadeInUp}
              >
                See It In <span className="gradient-text drop-shadow-lg">Action</span>
              </motion.h2>
              <motion.p
                className="text-lg lg:text-xl text-gray-300 font-light leading-relaxed"
                variants={fadeInUp}
              >
                From upload to answer in seconds. Experience the power of AI-driven knowledge retrieval.
              </motion.p>
            </FloatingCard>
          </motion.div>

          <FloatingCard delay={0.3}>
            <InteractiveDemo />
          </FloatingCard>
        </div>
      </section>

      {/* Stats Section - Enhanced with better spacing and background */}
      <section className="py-24 bg-gradient-to-b from-black to-gray-900 relative overflow-hidden">
        <div className="absolute inset-0 bg-mesh opacity-40" />
        <div className="absolute top-0 left-1/3 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FloatingCard delay={0.1}>
              <CountUpStat
                end={99.9}
                decimals={1}
                suffix="%"
                label="Uptime"
                description="Always available when you need it"
              />
            </FloatingCard>
            <FloatingCard delay={0.2}>
              <CountUpStat
                end={250}
                suffix="ms"
                label="Avg Response Time"
                description="Lightning-fast query processing"
              />
            </FloatingCard>
            <FloatingCard delay={0.3}>
              <CountUpStat
                end={50}
                suffix="K+"
                label="Documents Processed"
                description="Trusted by leading organizations"
              />
            </FloatingCard>
          </div>
        </div>
      </section>

      {/* Final CTA Section - Enhanced with better styling and spacing */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/25 via-purple-600/25 to-pink-600/25" />
        <div className="absolute inset-0 bg-mesh opacity-60" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-aurora" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl animate-aurora" style={{ animationDelay: '3s' }} />

        <div className="relative max-w-6xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <motion.div
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            variants={stagger}
          >
            <FloatingCard delay={0.1} className="max-w-4xl mx-auto mb-12">
              <motion.h2
                className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 text-display leading-tight"
                variants={fadeInUp}
              >
                Ready to Transform Your{' '}
                <span className="gradient-text drop-shadow-lg">Knowledge Management?</span>
              </motion.h2>
              <motion.p
                className="text-lg lg:text-xl text-gray-200 font-light leading-relaxed"
                variants={fadeInUp}
              >
                Join thousands of organizations using AstraRAG to unlock the power of their documents.
                Start your free trial today - no credit card required.
              </motion.p>
            </FloatingCard>

            <motion.div variants={fadeInUp} className="flex flex-col sm:flex-row gap-6 justify-center">
              <FloatingCard delay={0.3} className="inline-block">
                <Link href="/login">
                  <motion.button
                    className="px-10 py-5 bg-white text-gray-900 rounded-2xl font-bold text-lg shadow-2xl hover:shadow-white/30 transition-all duration-500 flex items-center gap-3 border border-white/20 w-full justify-center"
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    Get Started Free
                    <ArrowRight className="h-5 w-5" />
                  </motion.button>
                </Link>
              </FloatingCard>
              <FloatingCard delay={0.4} className="inline-block">
                <Link href="/contact">
                  <motion.button
                    className="px-10 py-5 glass-strong text-white rounded-2xl font-bold text-lg hover:bg-white/15 transition-all duration-500 border border-white/20 shadow-xl hover:shadow-white/10 w-full justify-center"
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    Talk to Sales
                  </motion.button>
                </Link>
              </FloatingCard>
            </motion.div>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  );
}