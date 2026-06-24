'use client';

import {cn} from '@/lib/utils';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
}

export function ChatMessage({role, content}: ChatMessageProps) {
  const isUser = role === 'user';

  return (
    <div className={cn('flex gap-3', isUser ? 'flex-row-reverse' : 'flex-row')}>
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold',
          isUser
            ? 'bg-emerald-600 text-white'
            : 'bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-300'
        )}
      >
        {isUser ? 'T' : 'A'}
      </div>
      <div
        className={cn(
          'rounded-2xl px-4 py-3 max-w-[85%] text-sm leading-relaxed',
          isUser
            ? 'bg-emerald-600 text-white rounded-tr-sm'
            : 'bg-white dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200 rounded-tl-sm shadow-sm border border-zinc-100 dark:border-zinc-700'
        )}
      >
        <div className="whitespace-pre-wrap">{content}</div>
      </div>
    </div>
  );
}
