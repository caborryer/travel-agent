'use client';

import {useTranslations} from 'next-intl';
import {Badge} from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from '@/components/ui/card';

interface DestinationProps {
  destination: {
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
  };
}

export function DestinationCard({destination}: DestinationProps) {
  const t = useTranslations('Index');
  const d = destination;

  const scoreColors: Record<number, string> = {
    5: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
    4: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
    3: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
    2: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
    1: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  };

  return (
    <Card className="group border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800/80 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 cursor-pointer">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-semibold text-base text-zinc-900 dark:text-zinc-100">
              {d.name}
            </h3>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              {d.country}
            </p>
          </div>
          <Badge
            className={`${scoreColors[d.value_score] || scoreColors[3]} text-xs font-semibold px-2 py-0.5`}
          >
            {t('valueScore')} {d.value_score}/5
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pb-3 space-y-2 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wide min-w-[5rem]">
            {t('estimatedPrice')}
          </span>
          <span className="font-semibold text-emerald-700 dark:text-emerald-300">
            {d.estimated_price} {d.currency}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wide min-w-[5rem]">
            {t('bestSeason')}
          </span>
          <span className="text-zinc-700 dark:text-zinc-300">{d.best_season}</span>
        </div>
        {d.weather_note && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wide min-w-[5rem]">
              Clima
            </span>
            <span className="text-zinc-600 dark:text-zinc-400">{d.weather_note}</span>
          </div>
        )}
        <div className="pt-1">
          <p className="text-xs text-zinc-500 dark:text-zinc-400 italic">
            {d.why_lowcost}
          </p>
        </div>
        {d.activities.length > 0 && (
          <div className="pt-1">
            <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wide mb-1">
              {t('activities')}
            </p>
            <div className="flex flex-wrap gap-1">
              {d.activities.map((a, i) => (
                <Badge key={i} variant="secondary" className="text-xs">
                  {a}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter className="pt-0 pb-3">
        <p className="text-[10px] text-zinc-400 dark:text-zinc-500">
          {t('source')}: {d.source?.slice(0, 40)}
          {d.source?.length > 40 ? '…' : ''}
        </p>
      </CardFooter>
    </Card>
  );
}
