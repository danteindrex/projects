'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import { DocumentDuplicateIcon, CheckIcon } from '@heroicons/react/24/outline';

interface MessageFormatterProps {
  content: string;
  messageType: 'user' | 'assistant' | 'system' | 'tool_call' | 'thinking';
  className?: string;
}

export default function MessageFormatter({ content, messageType, className = '' }: MessageFormatterProps) {
  const [copiedCode, setCopiedCode] = React.useState<string | null>(null);

  const handleCopyCode = async (code: string, blockId: string) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopiedCode(blockId);
      setTimeout(() => setCopiedCode(null), 2000);
    } catch (error) {
      console.error('Failed to copy code:', error);
    }
  };

  // Get appropriate colors for different message types
  const getColorClasses = () => {
    if (messageType === 'user') {
      return {
        text: 'text-black',
        heading: 'text-black',
        link: 'text-black hover:text-neutral-700',
        strong: 'text-black',
        emphasis: 'text-black',
        code: 'bg-neutral-100 text-black',
        blockquote: 'border-neutral-300 bg-neutral-100 text-black',
      };
    }
    return {
      text: 'text-neutral-800',
      heading: 'text-neutral-900',
      link: 'text-primary-regular hover:text-primary-dark',
      strong: 'text-neutral-900',
      emphasis: 'text-neutral-800',
      code: 'bg-neutral-100 text-neutral-800',
      blockquote: 'border-primary-regular bg-primary-regular/5 text-neutral-700',
    };
  };

  const colors = getColorClasses();

  // Custom components for react-markdown
  const components = {
    // Enhanced paragraph formatting
    p: ({ children, ...props }: any) => (
      <p className="mb-3 last:mb-0 leading-relaxed" {...props}>
        {children}
      </p>
    ),

    // Enhanced heading formatting
    h1: ({ children, ...props }: any) => (
      <h1 className={`text-lg sm:text-xl font-bold mb-3 sm:mb-4 mt-4 sm:mt-6 first:mt-0 ${colors.heading}`} {...props}>
        {children}
      </h1>
    ),
    h2: ({ children, ...props }: any) => (
      <h2 className={`text-base sm:text-lg font-semibold mb-2 sm:mb-3 mt-3 sm:mt-5 first:mt-0 ${colors.heading}`} {...props}>
        {children}
      </h2>
    ),
    h3: ({ children, ...props }: any) => (
      <h3 className={`text-sm sm:text-base font-semibold mb-2 mt-3 sm:mt-4 first:mt-0 ${colors.heading}`} {...props}>
        {children}
      </h3>
    ),

    // Enhanced list formatting
    ul: ({ children, ...props }: any) => (
      <ul className="mb-3 ml-4 space-y-1 list-disc" {...props}>
        {children}
      </ul>
    ),
    ol: ({ children, ...props }: any) => (
      <ol className="mb-3 ml-4 space-y-1 list-decimal" {...props}>
        {children}
      </ol>
    ),
    li: ({ children, ...props }: any) => (
      <li className="leading-relaxed" {...props}>
        {children}
      </li>
    ),

    // Enhanced blockquote formatting
    blockquote: ({ children, ...props }: any) => (
      <blockquote 
        className={`border-l-4 pl-4 py-2 my-3 italic ${colors.blockquote}`}
        {...props}
      >
        {children}
      </blockquote>
    ),

    // Enhanced table formatting
    table: ({ children, ...props }: any) => (
      <div className="overflow-x-auto my-3 rounded-lg border border-neutral-200">
        <table className="min-w-full" {...props}>
          {children}
        </table>
      </div>
    ),
    thead: ({ children, ...props }: any) => (
      <thead className="bg-neutral-50" {...props}>
        {children}
      </thead>
    ),
    th: ({ children, ...props }: any) => (
      <th className="px-2 sm:px-3 py-2 text-left text-xs sm:text-sm font-semibold text-neutral-900 border-b border-neutral-200" {...props}>
        {children}
      </th>
    ),
    td: ({ children, ...props }: any) => (
      <td className="px-2 sm:px-3 py-2 text-xs sm:text-sm text-neutral-700 border-b border-neutral-200" {...props}>
        {children}
      </td>
    ),

    // Enhanced inline code formatting
    code: ({ node, inline, className, children, ...props }: any) => {
      if (inline) {
        return (
          <code 
            className={`px-1.5 py-0.5 rounded text-sm font-mono ${colors.code}`}
            {...props}
          >
            {children}
          </code>
        );
      }

      // Block code with copy functionality
      const match = /language-(\w+)/.exec(className || '');
      const language = match ? match[1] : '';
      const codeString = String(children).replace(/\n$/, '');
      const blockId = `code-${Math.random().toString(36).substr(2, 9)}`;

      return (
        <div className="relative group my-3 sm:my-4">
          <div className="flex items-center justify-between bg-neutral-800 text-neutral-200 px-3 sm:px-4 py-2 rounded-t-lg text-xs sm:text-sm">
            <span className="font-mono truncate mr-2">{language || 'code'}</span>
            <button
              onClick={() => handleCopyCode(codeString, blockId)}
              className="flex items-center space-x-1 text-neutral-400 hover:text-white transition-colors duration-200 flex-shrink-0"
              aria-label="Copy code to clipboard"
            >
              {copiedCode === blockId ? (
                <CheckIcon className="w-3 h-3 sm:w-4 sm:h-4" />
              ) : (
                <DocumentDuplicateIcon className="w-3 h-3 sm:w-4 sm:h-4" />
              )}
              <span className="text-xs hidden sm:inline">
                {copiedCode === blockId ? 'Copied!' : 'Copy'}
              </span>
            </button>
          </div>
          <pre className="bg-neutral-900 text-neutral-100 p-3 sm:p-4 rounded-b-lg overflow-x-auto text-xs sm:text-sm">
            <code className={className} {...props}>
              {children}
            </code>
          </pre>
        </div>
      );
    },

    // Enhanced link formatting
    a: ({ children, href, ...props }: any) => (
      <a
        href={href}
        className={`${colors.link} underline underline-offset-2 transition-colors duration-200`}
        target="_blank"
        rel="noopener noreferrer"
        {...props}
      >
        {children}
      </a>
    ),

    // Enhanced strong/bold formatting
    strong: ({ children, ...props }: any) => (
      <strong className={`font-semibold ${colors.strong}`} {...props}>
        {children}
      </strong>
    ),

    // Enhanced emphasis/italic formatting
    em: ({ children, ...props }: any) => (
      <em className={`italic ${colors.emphasis}`} {...props}>
        {children}
      </em>
    ),

    // Horizontal rule formatting
    hr: ({ ...props }: any) => (
      <hr className="border-neutral-200 my-6" {...props} />
    ),
  };

  // For simple text messages, check if it's likely markdown
  const isLikelyMarkdown = (text: string) => {
    const markdownIndicators = [
      /#{1,6}\s+.+/,           // Headers
      /\*\*.+\*\*/,            // Bold
      /\*.+\*/,                // Italic
      /`[^`]+`/,               // Inline code
      /```[\s\S]*```/,         // Code blocks
      /^\s*[-*+]\s+/m,         // Unordered lists
      /^\s*\d+\.\s+/m,         // Ordered lists
      /\[.+\]\(.+\)/,          // Links
      /^\s*>/m,                // Blockquotes
      /\|.+\|/,                // Tables
    ];
    
    return markdownIndicators.some(pattern => pattern.test(text));
  };

  // Preserve line breaks for non-markdown text
  const formatPlainText = (text: string) => {
    return text.split('\n').map((line, index) => (
      <React.Fragment key={index}>
        {line}
        {index < text.split('\n').length - 1 && <br />}
      </React.Fragment>
    ));
  };

  // Determine the appropriate text color based on message type
  const getTextColorClass = () => {
    switch (messageType) {
      case 'user':
        return 'text-black';
      case 'assistant':
        return 'text-neutral-800';
      case 'system':
        return 'text-blue-800';
      case 'tool_call':
        return 'text-blue-800';
      case 'thinking':
        return 'text-yellow-800';
      default:
        return 'text-neutral-800';
    }
  };

  const shouldUseMarkdown = isLikelyMarkdown(content) || messageType === 'assistant';

  return (
    <div className={`${className} ${getTextColorClass()}`}>
      {shouldUseMarkdown ? (
        <ReactMarkdown
          components={components}
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeHighlight, rehypeRaw]}
        >
          {content}
        </ReactMarkdown>
      ) : (
        <div className="leading-relaxed">
          {formatPlainText(content)}
        </div>
      )}
    </div>
  );
}