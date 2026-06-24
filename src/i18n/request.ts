import {cookies} from 'next/headers';
import {hasLocale} from 'next-intl';
import {getRequestConfig} from 'next-intl/server';
import {routing} from './routing';
import esMessages from '../messages/es.json';
import enMessages from '../messages/en.json';

const messageMap = {
  es: esMessages,
  en: enMessages,
} as const;

export default getRequestConfig(async () => {
  const cookieStore = await cookies();
  const cookieLocale = cookieStore.get('NEXT_LOCALE')?.value;
  const locale = hasLocale(routing.locales, cookieLocale)
    ? cookieLocale
    : routing.defaultLocale;

  return {
    locale,
    messages: messageMap[locale as keyof typeof messageMap],
    getMessageFallback({namespace, key}) {
      const path = [namespace, key].filter(Boolean).join('.');
      if (path === 'Index.openSource') {
        return locale === 'es' ? 'Ver fuente →' : 'View source →';
      }
      if (path === 'Index.openSourceFor') {
        return locale === 'es' ? 'Ver fuente' : 'View source';
      }
      return path;
    },
  };
});
