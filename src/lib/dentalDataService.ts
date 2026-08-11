// src/lib/dentalDataService.ts — 口腔视界数据服务
// 优先从 Supabase 读取真实数据（dental_papers 等表），
// 未配置 Supabase 或读取失败时回落到本地模拟数据。
import { supabase } from './supabaseClient';
import {
  dentalPapers,
  dentalJournals,
  dentalBooks,
  dentalVideos,
  dentalCases,
  nursingItems,
  scanItems,
} from '../data/dentalData';

// 论文：优先 Supabase，回落本地
export async function loadPapers(): Promise<typeof dentalPapers> {
  if (supabase) {
    try {
      const { data, error } = await supabase
        .from('dental_papers')
        .select('*')
        .order('published_on', { ascending: false })
        .limit(50);
      if (!error && data && data.length > 0) {
        return (data as any[]).map((r) => ({
          id: r.id || r.pmid,
          title: r.title,
          authors: r.authors || '',
          journal: r.journal || '',
          date: (r.published_on || '').slice(5, 10), // 'YYYY-MM-DD' → 'MM-DD'
          url: r.url || '#',
          abstract: r.abstract || '',
          type: (r.paper_type as any) || '研究',
          tags: Array.isArray(r.tags) ? r.tags : [],
          isNew: r.is_new,
          pmid: r.pmid,
        }));
      }
    } catch (e) {
      console.warn('[DentaScope] 读取论文失败，使用本地数据', e);
    }
  }
  return dentalPapers;
}

// 护理：优先 Supabase，回落本地
export async function loadNursing(): Promise<typeof nursingItems> {
  if (supabase) {
    try {
      const { data, error } = await supabase
        .from('dental_nursing')
        .select('*')
        .order('published_on', { ascending: false })
        .limit(30);
      if (!error && data && data.length > 0) {
        return (data as any[]).map((r) => ({
          id: r.id,
          title: r.title,
          category: r.category as any,
          date: (r.published_on || '').slice(5, 10),
          summary: r.summary || '',
          url: r.url || '#',
        }));
      }
    } catch (e) {
      console.warn('[DentaScope] 读取护理数据失败，使用本地数据', e);
    }
  }
  return nursingItems;
}

// 病例：优先 Supabase，回落本地
export async function loadCases(): Promise<typeof dentalCases> {
  if (supabase) {
    try {
      const { data, error } = await supabase
        .from('dental_cases')
        .select('*')
        .order('published_on', { ascending: false })
        .limit(30);
      if (!error && data && data.length > 0) {
        return (data as any[]).map((r) => ({
          id: r.id,
          title: r.title,
          patient: r.patient || '',
          diagnosis: r.diagnosis || '',
          specialty: r.specialty,
          date: (r.published_on || '').slice(5, 10),
          url: r.url || '#',
          image: '🦷',
          summary: r.summary || '',
        }));
      }
    } catch (e) {
      console.warn('[DentaScope] 读取病例失败，使用本地数据', e);
    }
  }
  return dentalCases;
}

// 视频：优先 Supabase，回落本地
export async function loadVideos(): Promise<typeof dentalVideos> {
  if (supabase) {
    try {
      const { data, error } = await supabase
        .from('dental_videos')
        .select('*')
        .order('published_on', { ascending: false })
        .limit(30);
      if (!error && data && data.length > 0) {
        return (data as any[]).map((r) => ({
          id: r.id,
          title: r.title,
          channel: r.channel || '',
          date: (r.published_on || '').slice(5, 10),
          url: r.url || '#',
          duration: r.duration || '',
          category: (r.category as any) || '讲座',
        }));
      }
    } catch (e) {
      console.warn('[DentaScope] 读取视频失败，使用本地数据', e);
    }
  }
  return dentalVideos;
}

// 书：优先 Supabase，回落本地
export async function loadBooks(): Promise<typeof dentalBooks> {
  if (supabase) {
    try {
      const { data, error } = await supabase
        .from('dental_books')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(30);
      if (!error && data && data.length > 0) {
        return (data as any[]).map((r) => ({
          id: r.id,
          title: r.title,
          author: r.author || '',
          cover: '📚',
          year: r.publish_year || 0,
          category: (r.category as any) || '教科书',
          url: r.url || '#',
          description: r.description || '',
        }));
      }
    } catch (e) {
      console.warn('[DentaScope] 读取书库失败，使用本地数据', e);
    }
  }
  return dentalBooks;
}

// 影像：优先 Supabase，回落本地
export async function loadScans(): Promise<typeof scanItems> {
  if (supabase) {
    try {
      const { data, error } = await supabase
        .from('dental_scans')
        .select('*')
        .order('published_on', { ascending: false })
        .limit(30);
      if (!error && data && data.length > 0) {
        return (data as any[]).map((r) => ({
          id: r.id,
          title: r.title,
          modality: (r.modality as any) || '全景片',
          date: (r.published_on || '').slice(5, 10),
          finding: r.finding || '',
          url: r.url || '#',
        }));
      }
    } catch (e) {
      console.warn('[DentaScope] 读取影像失败，使用本地数据', e);
    }
  }
  return scanItems;
}

export { dentalJournals };
