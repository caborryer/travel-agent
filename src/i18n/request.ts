import {appendFileSync} from 'fs';
import {getRequestConfig} from 'next-intl/server';
import {routing} from './routing';
import esMessages from '../messages/es.json';
import enMessages from '../messages/en.json';

const messageMap = {
  es: esMessages,
  en: enMessages,
} as const;

const DEBUG_LOG = '/Users/andreacorrales/travel-agent/.cursor/debug-df77db.log';

function debugLog(hypothesisId: string, message: string, data: Record<string, unknown>) {
  // #region agent log
  try {
    appendFileSync(
      DEBUG_LOG,
      `${JSON.stringify({
        sessionId: 'df77db',
        hypothesisId,
        location: 'request.ts',
        message,
        data,
        timestamp: Date.now(),
      })}\n`,
    );
  } catch {
    // ignore logging failures
  }
  // #endregion
}

export default getRequestConfig(async ({requestLocale}) => {
  let locale = await requestLocale;
  if (!locale || !routing.locales.includes(locale as 'es' | 'en')) {
    locale = routing.defaultLocale;
  }

  const messages = messageMap[locale as keyof typeof messageMap];
  const indexKeys = Object.keys(messages.Index ?? {});

  debugLog('H1', 'messages loaded', {
    locale,
    hasOpenSource: indexKeys.includes('openSource'),
    hasOpenSourceFor: indexKeys.includes('openSourceFor'),
    indexKeyCount: indexKeys.length,
  });

  return {
    locale,
    messages,
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
