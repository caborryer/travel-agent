import {useTranslations} from 'next-intl';

export function Footer() {
  const t = useTranslations('Index');

  return (
    <footer className="border-t border-zinc-200 dark:border-zinc-800 py-6">
      <div className="max-w-5xl mx-auto px-4 text-center text-sm text-zinc-500 dark:text-zinc-500">
        {t('footer')}
      </div>
    </footer>
  );
}
