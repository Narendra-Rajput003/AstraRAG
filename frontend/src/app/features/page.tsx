'use client';

import { motion } from 'framer-motion';
import { FileText, Search, Shield, Zap, Database, Brain, Lock, BarChart3, Cloud, Users } from 'lucide-react';

export default function Features() {
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
      icon: <FileText className="h-12 w-12 text-blue-500" />,
      title: "Multi-Format Document Support",
      description: "Upload and process PDF, DOCX, TXT, and other document formats with automatic text extraction and parsing.",
      details: ["PDF parsing with layout preservation", "DOCX document structure recognition", "Text extraction from images", "Support for 20+ file formats"]
    },
    {
      icon: <Brain className="h-12 w-12 text-purple-500" />,
      title: "Advanced AI Processing",
      description: "Powered by state-of-the-art language models and vector embeddings for intelligent document understanding.",
      details: ["GPT-4 and Claude integration", "Custom fine-tuned models", "Multi-language support", "Context-aware processing"]
    },
    {
      icon: <Search className="h-12 w-12 text-green-500" />,
      title: "Intelligent Search & Retrieval",
      description: "Find exactly what you need with semantic search, keyword matching, and relevance ranking.",
      details: ["Semantic search capabilities", "Hybrid search (keyword + vector)", "Relevance scoring", "Multi-document search"]
    },
    {
      icon: <Shield className="h-12 w-12 text-red-500" />,
      title: "Enterprise Security",
      description: "Bank-grade security with encryption, access controls, and compliance features.",
      details: ["End-to-end encryption", "Role-based access control", "Audit logging", "GDPR compliance"]
    },
    {
      icon: <Zap className="h-12 w-12 text-yellow-500" />,
      title: "High Performance",
      description: "Optimized for speed with caching, parallel processing, and scalable architecture.",
      details: ["Sub-second response times", "Redis caching layer", "Horizontal scaling", "99.9% uptime SLA"]
    },
    {
      icon: <Database className="h-12 w-12 text-orange-500" />,
      title: "Scalable Vector Database",
      description: "Built on Milvus and other vector databases for efficient similarity search at scale.",
      details: ["Milvus vector database", "FAISS integration", "Distributed indexing", "Real-time updates"]
    },
    {
      icon: <Lock className="h-12 w-12 text-indigo-500" />,
      title: "PII Detection & Anonymization",
      description: "Automatically detect and anonymize sensitive information using advanced NLP models.",
      details: ["Microsoft Presidio integration", "Custom PII patterns", "Anonymization techniques", "Compliance reporting"]
    },
    {
      icon: <BarChart3 className="h-12 w-12 text-pink-500" />,
      title: "Analytics & Insights",
      description: "Comprehensive analytics dashboard with usage metrics, performance insights, and reporting.",
      details: ["Real-time dashboards", "Usage analytics", "Performance metrics", "Custom reports"]
    },
    {
      icon: <Cloud className="h-12 w-12 text-cyan-500" />,
      title: "Cloud Integration",
      description: "Seamless integration with AWS S3, Azure Blob Storage, and other cloud storage providers.",
      details: ["AWS S3 integration", "Azure Blob Storage", "Google Cloud Storage", "Multi-cloud support"]
    },
    {
      icon: <Users className="h-12 w-12 text-emerald-500" />,
      title: "Multi-User Collaboration",
      description: "Team collaboration features with shared workspaces, permissions, and version control.",
      details: ["Shared document libraries", "Team permissions", "Version history", "Collaboration tools"]
    }
  ];

  return (
    <div className="min-h-screen bg-black">
      {/* Hero Section */}
      <section className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-purple-900/20 to-black" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center"
            initial="initial"
            animate="animate"
            variants={stagger}
          >
            <motion.h1
              className="text-4xl sm:text-6xl font-bold text-white mb-6"
              variants={fadeInUp}
            >
              Powerful Features for
              <br />
              <span className="gradient-text">Modern Knowledge Management</span>
            </motion.h1>

            <motion.p
              className="text-xl text-gray-400 mb-8 max-w-3xl mx-auto leading-relaxed"
              variants={fadeInUp}
            >
              Discover the comprehensive suite of features that make AstraRAG the leading choice
              for AI-powered document processing and intelligent Q&A systems.
            </motion.p>
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-24 bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 gap-12"
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            variants={stagger}
          >
            {features.map((feature, index) => (
              <motion.div
                key={index}
                className="bg-gray-800 p-8 rounded-xl hover:bg-gray-750 transition-all duration-200 hover:shadow-2xl"
                variants={fadeInUp}
                whileHover={{ y: -5 }}
              >
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    {feature.icon}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-semibold text-white mb-3">
                      {feature.title}
                    </h3>
                    <p className="text-gray-400 mb-6 leading-relaxed">
                      {feature.description}
                    </p>

                    <div className="space-y-2">
                      {feature.details.map((detail, detailIndex) => (
                        <div key={detailIndex} className="flex items-center text-gray-300">
                          <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mr-3 flex-shrink-0" />
                          {detail}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Demo Section */}
      <section className="py-24 bg-black">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center mb-16"
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            variants={stagger}
          >
            <motion.h2
              className="text-3xl sm:text-4xl font-bold text-white mb-4"
              variants={fadeInUp}
            >
              See AstraRAG in Action
            </motion.h2>
            <motion.p
              className="text-xl text-gray-400 max-w-2xl mx-auto"
              variants={fadeInUp}
            >
              Experience the power of intelligent document processing and Q&A
            </motion.p>
          </motion.div>

          <motion.div
            className="bg-gray-800 rounded-xl p-8 max-w-4xl mx-auto"
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            variants={fadeInUp}
          >
            <div className="text-center text-gray-400 mb-8">
              Interactive demo coming soon...
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
              <div className="bg-gray-700 p-6 rounded-lg">
                <FileText className="h-8 w-8 text-blue-500 mx-auto mb-4" />
                <h3 className="text-white font-semibold mb-2">Upload Documents</h3>
                <p className="text-gray-400 text-sm">Drag & drop your files</p>
              </div>

              <div className="bg-gray-700 p-6 rounded-lg">
                <Search className="h-8 w-8 text-purple-500 mx-auto mb-4" />
                <h3 className="text-white font-semibold mb-2">Ask Questions</h3>
                <p className="text-gray-400 text-sm">Natural language queries</p>
              </div>

              <div className="bg-gray-700 p-6 rounded-lg">
                <Brain className="h-8 w-8 text-green-500 mx-auto mb-4" />
                <h3 className="text-white font-semibold mb-2">Get Answers</h3>
                <p className="text-gray-400 text-sm">AI-powered responses</p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}