'use client';

import {NextIntlClientProvider} from 'next-intl';
import {useEffect, useState} from 'react';
import esMessages from '@/messages/es.json';
import enMessages from '@/messages/en.json';

type Locale = 'es' | 'en';

export function LocaleProvider({children}: {children: React.ReactNode}) {
  const [locale, setLocale] = useState<Locale>('es');

  useEffect(() => {
    const match = document.cookie.match(/(?:^|;\s*)NEXT_LOCALE=(es|en)/);
    if (match?.[1]) setLocale(match[1] as Locale);

    const onLocaleChange = (event: Event) => {
      const next = (event as CustomEvent<Locale>).detail;
      if (next === 'es' || next === 'en') setLocale(next);
    };

    window.addEventListener('travel-agent:locale', onLocaleChange);
    return () => window.removeEventListener('travel-agent:locale', onLocaleChange);
  }, []);

  const messages = locale === 'en' ? enMessages : esMessages;

  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      {children}
    </NextIntlClientProvider>
  );
}
