export function descriptionText(value = '') {
  return value.replace(/<br\s*\/?\s*>|<\/stats>|<hr\s*\/?\s*>/gi, '\n')
    .replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"')
    .replace(/@[\w.*]+@|\{\{[^}]+\}\}/g, '수치 미제공').trim();
}
