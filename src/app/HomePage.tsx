'use client';

import {useState, useRef, useEffect} from 'react';
import {useTranslations, useLocale} from 'next-intl';
import {ChatMessage} from '@/components/chat/ChatMessage';
import {ChatInput} from '@/components/chat/ChatInput';
import {DestinationCard} from '@/components/destinations/DestinationCard';
import {Navbar} from '@/components/layout/Navbar';
import {Footer} from '@/components/layout/Footer';

interface Destination {
  name: string;
  country: string;
  estimated_price: string;
  currency: string;
  best_season: string;
  why_lowcost: string;
  value_score: number;
  activities: string[];
  source: string;
  weather_note?: string;
  image_url?: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  destinations?: Destination[];
}

export default function HomePage() {
  const t = useTranslations('Index');
  const locale = useLocale();

  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: locale === 'es'
        ? '¡Hola! Soy tu asistente de viajes. Cuéntame qué tipo de viaje buscas: ¿ciudad de origen, presupuesto, fechas, intereses?'
        : 'Hi! I\'m your travel assistant. Tell me what kind of trip you\'re looking for: origin city, budget, dates, interests?',
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({behavior: 'smooth'});
  }, [messages]);

  const handleSend = async (message: string) => {
    const userMsg: Message = {role: 'user', content: message};
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message}),
      });

      if (!res.ok) throw new Error('Network error');

      const data = await res.json();
      const assistantMsg: Message = {
        role: 'assistant',
        content: data.message,
        destinations: data.destinations,
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch {
      setMessages(prev => [
        ...prev,
        {role: 'assistant', content: t('chatError')},
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <main className="flex-1 w-full max-w-5xl mx-auto px-4 pt-24 pb-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-emerald-900 dark:text-emerald-100">
            {t('heroTitle')}
          </h1>
          <p className="mt-3 text-lg text-zinc-600 dark:text-zinc-400">
            {t('heroTagline')}
          </p>
        </div>

        <div className="space-y-4 mb-6">
          {messages.map((msg, i) => (
            <div key={i}>
              <ChatMessage role={msg.role} content={msg.content} />
              {msg.destinations && msg.destinations.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
                  {msg.destinations.map((dest, j) => (
                    <DestinationCard key={j} destination={dest} />
                  ))}
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex items-center gap-2 text-sm text-zinc-500 dark:text-zinc-400 animate-pulse ml-10">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-bounce" />
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-bounce [animation-delay:0.1s]" />
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-bounce [animation-delay:0.2s]" />
              <span className="ml-2">{t('chatThinking')}</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <ChatInput onSend={handleSend} isLoading={isLoading} placeholder={t('chatPlaceholder')} />
      </main>
      <Footer />
    </>
  );
}
