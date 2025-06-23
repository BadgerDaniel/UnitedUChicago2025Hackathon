import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownMessageProps {
  content: string;
  className?: string;
}

const MarkdownMessage: React.FC<MarkdownMessageProps> = ({ content, className = '' }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      className={`markdown-content ${className}`}
      components={{
        // Headings
        h1: ({ children }) => <h1 className="text-2xl font-bold mb-4 mt-2">{children}</h1>,
        h2: ({ children }) => <h2 className="text-xl font-bold mb-3 mt-2">{children}</h2>,
        h3: ({ children }) => <h3 className="text-lg font-bold mb-2 mt-2">{children}</h3>,
        h4: ({ children }) => <h4 className="text-base font-bold mb-2 mt-1">{children}</h4>,
        
        // Paragraphs and text
        p: ({ children }) => <p className="mb-3 leading-relaxed">{children}</p>,
        strong: ({ children }) => <strong className="font-bold">{children}</strong>,
        em: ({ children }) => <em className="italic">{children}</em>,
        
        // Lists
        ul: ({ children }) => <ul className="list-disc pl-6 mb-3 space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-6 mb-3 space-y-1">{children}</ol>,
        li: ({ children }) => <li className="leading-relaxed">{children}</li>,
        
        // Code
        code: ({ inline, children }) => {
          if (inline) {
            return <code className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-sm font-mono">{children}</code>;
          }
          return (
            <pre className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 overflow-x-auto mb-3">
              <code className="text-sm font-mono">{children}</code>
            </pre>
          );
        },
        
        // Blockquotes
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 my-3 italic">
            {children}
          </blockquote>
        ),
        
        // Tables
        table: ({ children }) => (
          <div className="overflow-x-auto mb-3">
            <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-600">
              {children}
            </table>
          </div>
        ),
        thead: ({ children }) => <thead className="bg-gray-100 dark:bg-gray-800">{children}</thead>,
        tbody: ({ children }) => <tbody>{children}</tbody>,
        tr: ({ children }) => <tr className="border-b border-gray-300 dark:border-gray-600">{children}</tr>,
        th: ({ children }) => <th className="px-4 py-2 text-left font-semibold">{children}</th>,
        td: ({ children }) => <td className="px-4 py-2">{children}</td>,
        
        // Links
        a: ({ href, children }) => (
          <a 
            href={href} 
            className="text-blue-600 dark:text-blue-400 hover:underline"
            target="_blank" 
            rel="noopener noreferrer"
          >
            {children}
          </a>
        ),
        
        // Horizontal rules
        hr: () => <hr className="border-t border-gray-300 dark:border-gray-600 my-4" />,
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

export default MarkdownMessage;