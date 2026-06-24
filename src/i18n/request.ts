import {getRequestConfig} from 'next-intl/server';
import {routing} from './routing';
import esMessages from '../messages/es.json';

export default getRequestConfig(async () => ({
  locale: routing.defaultLocale,
  messages: esMessages,
  getMessageFallback({namespace, key}) {
    const path = [namespace, key].filter(Boolean).join('.');
    if (path === 'Index.openSource') return 'Ver fuente →';
    if (path === 'Index.openSourceFor') return 'Ver fuente';
    return path;
  },
}));
