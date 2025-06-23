// Simple markdown to HTML converter
export function parseSimpleMarkdown(text: string): string {
  let html = text;
  
  // Headers (#### -> h4, ### -> h3, ## -> h2, # -> h1)
  html = html.replace(/^#### (.+)$/gm, '<h4 class="text-base font-bold mb-2 mt-1">$1</h4>');
  html = html.replace(/^### (.+)$/gm, '<h3 class="text-lg font-bold mb-2 mt-2">$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold mb-3 mt-2">$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold mb-4 mt-2">$1</h1>');
  
  // Bold text **text**
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  
  // Italic text *text*
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  
  // Bullet points (convert lines starting with * to list items)
  // First, find all bullet point blocks
  html = html.replace(/((?:^\* .+$\n?)+)/gm, (match) => {
    const items = match.trim().split('\n').map(line => 
      line.replace(/^\* (.+)$/, '<li class="leading-relaxed">$1</li>')
    ).join('\n');
    return `<ul class="list-disc pl-6 mb-3 space-y-1">\n${items}\n</ul>`;
  });
  
  // Numbered lists (convert lines starting with number. to list items)
  html = html.replace(/((?:^\d+\. .+$\n?)+)/gm, (match) => {
    const items = match.trim().split('\n').map(line => 
      line.replace(/^\d+\. (.+)$/, '<li class="leading-relaxed">$1</li>')
    ).join('\n');
    return `<ol class="list-decimal pl-6 mb-3 space-y-1">\n${items}\n</ol>`;
  });
  
  // Inline code `code`
  html = html.replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-sm font-mono">$1</code>');
  
  // Horizontal rules (---)
  html = html.replace(/^---$/gm, '<hr class="border-t border-gray-300 dark:border-gray-600 my-4" />');
  
  // Paragraphs (add spacing between blocks)
  html = html.replace(/\n\n/g, '</p><p class="mb-3 leading-relaxed">');
  html = `<p class="mb-3 leading-relaxed">${html}</p>`;
  
  // Clean up empty paragraphs
  html = html.replace(/<p[^>]*>\s*<\/p>/g, '');
  
  return html;
}