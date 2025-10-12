'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { FileText, Download, ExternalLink } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';

// Dynamically import Swagger UI to avoid SSR issues
const SwaggerUI = dynamic(() => import('swagger-ui-react'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  )
});

import 'swagger-ui-react/swagger-ui.css';

const APIDocsPage: React.FC = () => {
  return (
    <ErrorBoundary>
      <APIDocsPageContent />
    </ErrorBoundary>
  );
};

const APIDocsPageContent: React.FC = () => {
  const { user } = useAuth();
  const [swaggerSpec, setSwaggerSpec] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadSwaggerSpec();
  }, []);

  const loadSwaggerSpec = async () => {
    try {
      // In a real implementation, this would fetch from your API
      // For now, we'll create a basic spec
      const spec = {
        openapi: "3.0.3",
        info: {
          title: "AstraRAG API",
          description: "Comprehensive API documentation for the AstraRAG document management and RAG system",
          version: "1.0.0",
          contact: {
            name: "API Support",
            email: "support@astrarag.com"
          },
          license: {
            name: "MIT",
            url: "https://opensource.org/licenses/MIT"
          }
        },
        servers: [
          {
            url: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
            description: "Development server"
          }
        ],
        security: [
          {
            bearerAuth: []
          }
        ],
        components: {
          securitySchemes: {
            bearerAuth: {
              type: "http",
              scheme: "bearer",
              bearerFormat: "JWT"
            }
          },
          schemas: {
            User: {
              type: "object",
              properties: {
                user_id: { type: "string", format: "uuid" },
                username: { type: "string" },
                role: { type: "string", enum: ["employee", "admin", "admin:hr", "superadmin"] },
                organization_id: { type: "integer" }
              }
            },
            Document: {
              type: "object",
              properties: {
                doc_id: { type: "string", format: "uuid" },
                filename: { type: "string" },
                content: { type: "string" },
                uploaded_by: { type: "string", format: "uuid" },
                uploaded_at: { type: "string", format: "date-time" },
                file_type: { type: "string" },
                file_size: { type: "integer" },
                status: { type: "string", enum: ["pending_review", "active", "rejected"] },
                metadata: { type: "object" },
                tags: { type: "array", items: { type: "string" } }
              }
            },
            SearchRequest: {
              type: "object",
              properties: {
                query: { type: "string", description: "Search query string" },
                filters: {
                  type: "object",
                  properties: {
                    file_type: { type: "string" },
                    uploaded_by: { type: "string", format: "uuid" },
                    status: { type: "string" },
                    tags: { type: "array", items: { type: "string" } },
                    date_from: { type: "string", format: "date" },
                    date_to: { type: "string", format: "date" },
                    file_size_min: { type: "integer" },
                    file_size_max: { type: "integer" }
                  }
                },
                sort_by: { type: "string", default: "uploaded_at" },
                sort_order: { type: "string", enum: ["asc", "desc"], default: "desc" },
                page: { type: "integer", default: 1 },
                size: { type: "integer", default: 20 }
              }
            },
            SearchResponse: {
              type: "object",
              properties: {
                documents: {
                  type: "array",
                  items: { $ref: "#/components/schemas/Document" }
                },
                total: { type: "integer" },
                page: { type: "integer" },
                size: { type: "integer" },
                facets: {
                  type: "object",
                  properties: {
                    file_types: { type: "array", items: { type: "string" } },
                    uploaders: { type: "array", items: { type: "string" } },
                    statuses: { type: "array", items: { type: "string" } },
                    tags: { type: "array", items: { type: "string" } },
                    date_ranges: {
                      type: "array",
                      items: {
                        type: "object",
                        properties: {
                          key: { type: "string" },
                          count: { type: "integer" }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        },
        paths: {
          "/health": {
            get: {
              summary: "Health Check",
              description: "Check the health status of all system components",
              tags: ["System"],
              responses: {
                "200": {
                  description: "System health information",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          status: { type: "string", enum: ["healthy", "unhealthy"] },
                          database: { type: "string" },
                          redis: { type: "string" },
                          timestamp: { type: "string", format: "date-time" }
                        }
                      }
                    }
                  }
                }
              }
            }
          },
          "/auth/login": {
            post: {
              summary: "User Login",
              description: "Authenticate user and return access tokens",
              tags: ["Authentication"],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["email", "password"],
                      properties: {
                        email: { type: "string", format: "email" },
                        password: { type: "string", minLength: 8 }
                      }
                    }
                  }
                }
              },
              responses: {
                "200": {
                  description: "Login successful",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          user: { $ref: "#/components/schemas/User" },
                          tokens: {
                            type: "object",
                            properties: {
                              access_token: { type: "string" },
                              refresh_token: { type: "string" }
                            }
                          },
                          mfa_required: { type: "boolean" },
                          temp_token: { type: "string" }
                        }
                      }
                    }
                  }
                },
                "401": {
                  description: "Invalid credentials"
                }
              }
            }
          },
          "/auth/register": {
            post: {
              summary: "User Registration",
              description: "Register a new user using an invite token",
              tags: ["Authentication"],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["invite_token", "email", "password"],
                      properties: {
                        invite_token: { type: "string" },
                        email: { type: "string", format: "email" },
                        password: { type: "string", minLength: 8 }
                      }
                    }
                  }
                }
              },
              responses: {
                "200": {
                  description: "Registration successful"
                },
                "400": {
                  description: "Invalid invite token or registration data"
                }
              }
            }
          },
          "/qa/ask": {
            post: {
              summary: "Query RAG System",
              description: "Ask questions about uploaded documents using RAG",
              tags: ["RAG", "Search"],
              security: [{ bearerAuth: [] }],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["query"],
                      properties: {
                        query: { type: "string", minLength: 1, maxLength: 1000 }
                      }
                    }
                  }
                }
              },
              responses: {
                "200": {
                  description: "Query response",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          answer: { type: "string" },
                          sources: {
                            type: "array",
                            items: {
                              type: "object",
                              properties: {
                                doc_id: { type: "string", format: "uuid" },
                                chunk_index: { type: "integer" }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                },
                "401": {
                  description: "Unauthorized"
                }
              }
            }
          },
          "/search/documents": {
            post: {
              summary: "Advanced Document Search",
              description: "Search documents with faceted filtering and pagination",
              tags: ["Search"],
              security: [{ bearerAuth: [] }],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: { $ref: "#/components/schemas/SearchRequest" }
                  }
                }
              },
              responses: {
                "200": {
                  description: "Search results",
                  content: {
                    "application/json": {
                      schema: { $ref: "#/components/schemas/SearchResponse" }
                    }
                  }
                },
                "401": {
                  description: "Unauthorized"
                }
              }
            }
          },
          "/policies/upload": {
            post: {
              summary: "Upload Document",
              description: "Upload a document for processing and indexing",
              tags: ["Documents"],
              security: [{ bearerAuth: [] }],
              requestBody: {
                required: true,
                content: {
                  "multipart/form-data": {
                    schema: {
                      type: "object",
                      properties: {
                        file: {
                          type: "string",
                          format: "binary",
                          description: "PDF file to upload"
                        }
                      }
                    }
                  }
                }
              },
              responses: {
                "200": {
                  description: "Document uploaded successfully",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          message: { type: "string" },
                          doc_id: { type: "string", format: "uuid" },
                          filename: { type: "string" },
                          status: { type: "string" }
                        }
                      }
                    }
                  }
                },
                "400": {
                  description: "Invalid file or upload error"
                },
                "401": {
                  description: "Unauthorized"
                }
              }
            }
          },
          "/analytics/user-activity": {
            get: {
              summary: "User Activity Analytics",
              description: "Get comprehensive user activity metrics",
              tags: ["Analytics"],
              security: [{ bearerAuth: [] }],
              parameters: [
                {
                  name: "days",
                  in: "query",
                  schema: { type: "integer", default: 30 },
                  description: "Number of days to analyze"
                }
              ],
              responses: {
                "200": {
                  description: "User activity data"
                },
                "401": {
                  description: "Unauthorized"
                },
                "403": {
                  description: "Insufficient permissions"
                }
              }
            }
          },
          "/admin/security-audit": {
            get: {
              summary: "Run Security Audit",
              description: "Execute comprehensive security audit (superadmin only)",
              tags: ["Security", "Admin"],
              security: [{ bearerAuth: [] }],
              responses: {
                "200": {
                  description: "Security audit results"
                },
                "401": {
                  description: "Unauthorized"
                },
                "403": {
                  description: "Superadmin access required"
                }
              }
            }
          }
        },
        tags: [
          {
            name: "Authentication",
            description: "User authentication and authorization endpoints"
          },
          {
            name: "RAG",
            description: "Retrieval-Augmented Generation endpoints"
          },
          {
            name: "Search",
            description: "Document search and filtering endpoints"
          },
          {
            name: "Documents",
            description: "Document upload and management endpoints"
          },
          {
            name: "Analytics",
            description: "System and user analytics endpoints"
          },
          {
            name: "Security",
            description: "Security audit and monitoring endpoints"
          },
          {
            name: "Admin",
            description: "Administrative endpoints"
          },
          {
            name: "System",
            description: "System health and monitoring endpoints"
          }
        ]
      };

      setSwaggerSpec(spec);
    } catch (error) {
      console.error('Failed to load API documentation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const downloadOpenAPISpec = () => {
    if (!swaggerSpec) return;

    const data = JSON.stringify(swaggerSpec, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'astrarag-api-spec.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
        <div className="text-center">
          <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-4">API Documentation</h1>
          <p className="text-gray-600">Please log in to view API documentation.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">API Documentation</h1>
            <p className="text-gray-600 mt-1">Complete OpenAPI specification for AstraRAG</p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={downloadOpenAPISpec}
              disabled={!swaggerSpec}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Download OpenAPI Spec
            </button>
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <ExternalLink className="h-4 w-4" />
              View Raw API
            </a>
          </div>
        </div>
      </div>

      {/* API Documentation */}
      <div className="p-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : swaggerSpec ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <SwaggerUI spec={swaggerSpec} />
          </div>
        ) : (
          <div className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Documentation Unavailable</h3>
            <p className="text-gray-600">Unable to load API documentation at this time.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default APIDocsPage;