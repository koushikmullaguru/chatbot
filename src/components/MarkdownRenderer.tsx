import React from 'react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  // Simple markdown parser for basic formatting
  const parseMarkdown = (text: string) => {
    let html = text;
    
    // Bold text: **text** -> <strong>text</strong>
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic text: *text* -> <em>text</em>
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Inline code: `code` -> <code>code</code>
    html = html.replace(/`(.*?)`/g, '<code class="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-sm font-mono">$1</code>');
    
    // Code blocks: ```code``` -> <pre><code>code</code></pre>
    html = html.replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg overflow-x-auto my-4"><code>$1</code></pre>');
    
    // Blockquotes: > text -> <blockquote>text</blockquote>
    html = html.replace(/^> (.*$)/gm, '<blockquote class="border-l-4 border-blue-500 pl-4 py-2 my-4 bg-blue-50 dark:bg-blue-900/20 italic">$1</blockquote>');
    
    // Unordered lists: - item -> <ul><li>item</li></ul>
    const lines = html.split('\n');
    let inList = false;
    let result = '';
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Check for list items
      if (line.match(/^[\s]*-[\s]+(.*$)/)) {
        const itemText = line.replace(/^[\s]*-[\s]+/, '');
        
        if (!inList) {
          result += '<ul class="list-disc pl-5 my-2">';
          inList = true;
        }
        
        result += `<li class="mb-1">${itemText}</li>`;
      } else {
        if (inList) {
          result += '</ul>';
          inList = false;
        }
        
        // Check for headers
        if (line.match(/^#{1,6}\s+(.*$)/)) {
          const level = line.match(/^#/g)?.length || 1;
          const headerText = line.replace(/^#{1,6}\s+/, '');
          const headerSize = Math.min(level, 6);
          result += `<h${headerSize} class="text-${headerSize === 1 ? '2xl' : headerSize === 2 ? 'xl' : headerSize === 3 ? 'lg' : 'md'} font-bold mt-4 mb-2">${headerText}</h${headerSize}>`;
        } else {
          // Regular paragraph
          if (line.trim() !== '') {
            result += `<p class="mb-2">${line}</p>`;
          }
        }
      }
    }
    
    // Close any open list
    if (inList) {
      result += '</ul>';
    }
    
    // Simple table parsing
    result = result.replace(/\|(.+)\|/g, (match, content) => {
      const cells = content.split('|').map(cell => cell.trim());
      const rowHtml = cells.map(cell => `<td class="border border-gray-300 px-2 py-1 text-sm">${cell}</td>`).join('');
      return `<tr>${rowHtml}</tr>`;
    });
    
    // Wrap table rows in table tags with proper responsive container
    result = result.replace(/<tr>([\s\S]*?)<\/tr>/g, (match) => {
      return `<div class="overflow-x-auto my-4"><table class="w-full max-w-full border-collapse border border-gray-300">${match}</table></div>`;
    });
    
    // Add table headers
    result = result.replace(/<table>/g, '<table class="w-full max-w-full border-collapse border border-gray-300"><thead class="bg-gray-100">');
    result = result.replace(/<\/table>/g, '</thead></table></div>');
    
    return result;
  };

  const parsedContent = parseMarkdown(content);

  return (
    <div
      className={`markdown-content ${className}`}
      dangerouslySetInnerHTML={{ __html: parsedContent }}
    />
  );
}