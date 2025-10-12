'use client';

import { motion } from 'framer-motion';
import { Upload, Cpu, Search, MessageSquare, ArrowRight, CheckCircle, FileText, Database, Brain } from 'lucide-react';

export default function HowItWorks() {
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

  const steps = [
    {
      step: 1,
      icon: <Upload className="h-12 w-12 text-blue-500" />,
      title: "Document Upload",
      description: "Upload your documents in various formats (PDF, DOCX, TXT, etc.) through our secure web interface.",
      details: [
        "Drag & drop interface for easy uploads",
        "Support for multiple file formats",
        "Batch upload capabilities",
        "File size validation and security checks"
      ],
      color: "from-blue-500 to-blue-600"
    },
    {
      step: 2,
      icon: <FileText className="h-12 w-12 text-purple-500" />,
      title: "Document Processing",
      description: "Our system automatically processes documents, extracting text and preparing them for analysis.",
      details: [
        "Text extraction from various formats",
        "Document structure recognition",
        "Metadata extraction",
        "Content validation and cleaning"
      ],
      color: "from-purple-500 to-purple-600"
    },
    {
      step: 3,
      icon: <Database className="h-12 w-12 text-green-500" />,
      title: "Vector Embeddings",
      description: "Documents are converted into vector embeddings using advanced AI models for semantic understanding.",
      details: [
        "State-of-the-art embedding models",
        "Semantic understanding of content",
        "Context preservation",
        "Scalable vector storage"
      ],
      color: "from-green-500 to-green-600"
    },
    {
      step: 4,
      icon: <Search className="h-12 w-12 text-orange-500" />,
      title: "Intelligent Indexing",
      description: "Content is indexed in vector databases for fast and accurate retrieval.",
      details: [
        "Vector database indexing",
        "Similarity search optimization",
        "Metadata indexing",
        "Real-time index updates"
      ],
      color: "from-orange-500 to-orange-600"
    },
    {
      step: 5,
      icon: <MessageSquare className="h-12 w-12 text-red-500" />,
      title: "Query Processing",
      description: "When you ask a question, our system finds the most relevant document sections.",
      details: [
        "Natural language query understanding",
        "Relevance ranking",
        "Multi-document search",
        "Context-aware retrieval"
      ],
      color: "from-red-500 to-red-600"
    },
    {
      step: 6,
      icon: <Brain className="h-12 w-12 text-indigo-500" />,
      title: "AI Response Generation",
      description: "Large language models generate accurate, contextual answers based on retrieved information.",
      details: [
        "Context-aware answer generation",
        "Source citation and verification",
        "Multi-step reasoning",
        "Answer confidence scoring"
      ],
      color: "from-indigo-500 to-indigo-600"
    }
  ];

  const technologies = [
    { name: "FastAPI", description: "High-performance Python web framework" },
    { name: "LangChain", description: "Framework for LLM applications" },
    { name: "Milvus", description: "Vector database for similarity search" },
    { name: "Redis", description: "In-memory data structure store" },
    { name: "PostgreSQL", description: "Advanced open source relational database" },
    { name: "Next.js", description: "React framework for production" }
  ];

  return (
    <div className="min-h-screen bg-black">
      {/* Hero Section */}
      <section className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-black via-gray-900 to-black" />
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
              How AstraRAG
              <br />
              <span className="gradient-text">Works</span>
            </motion.h1>

            <motion.p
              className="text-xl text-gray-400 mb-8 max-w-3xl mx-auto leading-relaxed"
              variants={fadeInUp}
            >
              From document upload to AI-powered answers: understand the complete workflow
              behind our revolutionary RAG system.
            </motion.p>
          </motion.div>
        </div>
      </section>

      {/* Process Steps */}
      <section className="py-24 bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="space-y-16"
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            variants={stagger}
          >
            {steps.map((step, index) => (
              <motion.div
                key={step.step}
                className={`flex flex-col ${index % 2 === 0 ? 'lg:flex-row' : 'lg:flex-row-reverse'} items-center gap-12`}
                variants={fadeInUp}
              >
                {/* Step Number and Icon */}
                <div className="flex-shrink-0">
                  <div className={`w-24 h-24 bg-gradient-to-r ${step.color} rounded-full flex items-center justify-center text-white font-bold text-2xl shadow-lg animate-pulse-glow`}>
                    {step.step}
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 text-center lg:text-left">
                  <div className="flex items-center justify-center lg:justify-start gap-4 mb-4">
                    {step.icon}
                    <h3 className="text-2xl sm:text-3xl font-bold text-white">
                      {step.title}
                    </h3>
                  </div>

                  <p className="text-lg text-gray-400 mb-6 leading-relaxed">
                    {step.description}
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {step.details.map((detail, detailIndex) => (
                      <div key={detailIndex} className="flex items-center text-gray-300">
                        <CheckCircle className="h-5 w-5 text-green-500 mr-3 flex-shrink-0" />
                        {detail}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Arrow for flow */}
                {index < steps.length - 1 && (
                  <div className="hidden lg:block flex-shrink-0">
                    <ArrowRight className="h-8 w-8 text-gray-600" />
                  </div>
                )}
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Technology Stack */}
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
              Technology Stack
            </motion.h2>
            <motion.p
              className="text-xl text-gray-400 max-w-2xl mx-auto"
              variants={fadeInUp}
            >
              Built with cutting-edge technologies for performance, scalability, and reliability
            </motion.p>
          </motion.div>

          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            variants={stagger}
          >
            {technologies.map((tech, index) => (
              <motion.div
                key={index}
                className="bg-gray-800 p-6 rounded-xl hover:bg-gray-750 transition-colors duration-200"
                variants={fadeInUp}
                whileHover={{ y: -5 }}
              >
                <h3 className="text-xl font-semibold text-white mb-2">{tech.name}</h3>
                <p className="text-gray-400">{tech.description}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Architecture Diagram Placeholder */}
      <section className="py-24 bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center"
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            variants={stagger}
          >
            <motion.h2
              className="text-3xl sm:text-4xl font-bold text-white mb-4"
              variants={fadeInUp}
            >
              System Architecture
            </motion.h2>
            <motion.div
              className="bg-gray-800 rounded-xl p-12 max-w-4xl mx-auto"
              variants={fadeInUp}
            >
              <div className="text-center text-gray-400">
                <Cpu className="h-16 w-16 mx-auto mb-4 text-blue-500" />
                <p className="text-lg">Detailed architecture diagram coming soon...</p>
                <p className="text-sm mt-2">Frontend (Next.js) → API Gateway → FastAPI → Vector DB → LLM</p>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}