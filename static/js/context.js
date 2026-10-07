'use strict';
(() => {
  const pct = value => Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : 'Unavailable';
  const usd = value => Number.isFinite(value) ? value.toLocaleString('en-US', {style:'currency',currency:'USD',maximumFractionDigits:2}) : 'Unavailable';
  const compactUsd = value => Number.isFinite(value) ? value.toLocaleString('en-US', {style:'currency',currency:'USD',notation:'compact',maximumFractionDigits:2}) : 'Unavailable';
  const add = (parent, tag, text, className='') => {const node=document.createElement(tag);node.textContent=text;node.className=className;parent.append(node);return node;};
  let request;
  let generation=0;
  const form=document.getElementById('valuation-form')||document.getElementById('suite-form');
  const result=document.getElementById('price-comparison');
  const box=document.getElementById('decision-context');
  function history(parent, reference, title, money=compactUsd) {
    if(!reference?.annual?.length)return;
    add(parent,'h3',title);
    const list=add(parent,'div','','reference-grid');
    for(const row of reference.annual) {
      const card=add(list,'article','','reference-card');
      add(card,'small',row.period_end);add(card,'strong',money(row.value));
      add(card,'span',`Year-over-year: ${pct(row.growth)}`);
    }
    add(parent,'p',`Historical CAGR: ${pct(reference.cagr)} across ${reference.annual.length-1} annual intervals. ${reference.source}.`,'help');
  }
  function lock(doc) {
    const checkbox=document.getElementById('edit-sourced');
    if(!checkbox)return;
    const blank=!doc?.source || doc.source.kind==='manual' && !doc.source.origin_kind && !doc.source.manual_overrides;
    checkbox.checked=false;
    const apply=()=>{
      const unlocked=checkbox.checked||blank;
      for(const input of form.querySelectorAll('input[name]')) {
        const name=input.name;
        const sourced=/^(company_name|sector|source_name|price|price_as_of|diluted_shares|shares_basis|bridge_as_of|short_term_debt|long_term_debt|cash|preferred_equity|minority_interest|other_nonoperating_assets|base_common_dividends|dividend_as_of|historical_as_of|historical_|peer_|h_|period_)/.test(name);
        if(!sourced||['checkbox','hidden','file'].includes(input.type))continue;
        input.readOnly=!unlocked;
        input.classList.toggle('sourced-input',!unlocked);
        const yearMatch=name.match(/_(\d)$/);
        let origin=doc.source?.name||'Manual input';
        let dated=`Retrieved ${doc.source?.retrieved_at||doc.source?.available_at||doc.valuation_date}`;
        if((name.startsWith('h_')||name.startsWith('period_'))&&yearMatch) dated=`Fiscal period ${doc.historical?.[Number(yearMatch[1])]?.period_end||'unavailable'}`;
        else if(name.startsWith('peer_')&&yearMatch) {
          const peer=doc.comparables?.[Number(yearMatch[1])];
          origin=peer?.source||origin;
          dated=`Peer observation ${peer?.as_of||'unavailable'}`;
        } else if(['price','price_as_of'].includes(name)) dated=`Market observation ${doc.market?.price_as_of||'unavailable'}`;
        else if(['base_common_dividends','dividend_as_of'].includes(name)) dated=`Dividend fiscal period ${doc.source?.common_dividends?.period_end||doc.dividend_as_of||'unavailable'}`;
        else if(name.startsWith('historical_')) dated=`Fiscal period ${doc.target?.historical_as_of||'unavailable'}`;
        else if(['diluted_shares','shares_basis'].includes(name)) dated=doc.market?.shares_basis||'Share basis unavailable';
        else if(['bridge_as_of','short_term_debt','long_term_debt','cash','preferred_equity','minority_interest','other_nonoperating_assets'].includes(name)) dated=`Balance-sheet period ${doc.bridge?.as_of||'unavailable'}`;
        input.title=`${origin} · ${dated}. Full metric provenance is in Source document and provenance. ${unlocked?'Editing enabled.':'Unlock sourced inputs to override.'}`;
      }
      document.getElementById('sourced-origin').textContent=blank?'Manual model: enter verified financials.':`${doc.source.name} · retrieved ${doc.source.retrieved_at||doc.source.available_at||doc.valuation_date}. ${unlocked?'Overrides enabled; changes remain distinct from provider observations.':'Financials are locked; forecast assumptions stay editable.'}`;
    };
    checkbox.onchange=apply;apply();
  }
  async function references(doc, parent, isResult, token) {
    if(doc.source?.kind==='synthetic'||doc.source?.origin_kind==='synthetic'||!doc.source?.name?.startsWith('Yahoo')) {
      add(parent,'p','Analyst consensus is available for automatically loaded real-company snapshots.','help');return;
    }
    const status=add(parent,'p','Loading analyst references…','help');
    request=new AbortController();
    try {
      const response=await fetch(`/api/references/${encodeURIComponent(doc.company.ticker)}`,{signal:request.signal});
      const data=await response.json();if(!response.ok)throw new Error(data.error||'Analyst references unavailable.');
      if(token!==generation)return;
      status.remove();
      if(isResult) {
        const target=Number(result.dataset.target);const current=doc.market.price;
        add(parent,'h3','Analyst consensus · 12-month target reference');
        const card=add(parent,'div','','reference-card');
        add(card,'strong',usd(data.target.mean));
        if(Number.isFinite(data.target.mean)&&data.target.mean>0) {
          add(card,'span',`${pct(data.target.mean/current-1)} vs. dated market price · ${pct(target/data.target.mean-1)} model 12-month target vs. consensus`);
        }
        add(card,'span',`Range: ${usd(data.target.low)} – ${usd(data.target.high)} · median ${usd(data.target.median)} · ${data.target.analysts??'Unknown'} analysts`);
        add(parent,'p',data.horizon,'help');
      } else if(form?.dataset.method!=='ddm') {
        add(parent,'h3','Analyst expected revenue growth');
        const grid=add(parent,'div','','reference-grid');
        for(const row of data.revenue) {
          const card=add(grid,'article','','reference-card');
          add(card,'small',`${row.period==='0y'?'Current fiscal year':'Next fiscal year'} · ends ${row.period_end}`);
          add(card,'strong',pct(row.growth));add(card,'span',`Revenue consensus ${compactUsd(row.average)} · ${row.analysts??'Unknown'} analysts`);
          add(card,'span',`Revenue range ${compactUsd(row.low)} – ${compactUsd(row.high)}`);
          if(row.year_ago_revenue>0)add(card,'span',`Growth range: ${pct(row.low!=null?row.low/row.year_ago_revenue-1:null)} – ${pct(row.high!=null?row.high/row.year_ago_revenue-1:null)} vs. provider prior-year revenue baseline`);
        }
        if(!data.revenue.length)add(parent,'p','Annual revenue consensus unavailable.','help');
        add(parent,'p','Consensus periods may differ from forecast years. Current-year consensus can refer to a completed fiscal year awaiting results. Use the dates; forecasts are not automatically copied or extended into years 3–5.','help');
      }
      if(!isResult && doc.source?.peer_suggestions?.length && Number.isFinite(data.market_cap) && data.market_cap>0) {
        add(parent,'p',`Target current reported market cap: ${compactUsd(data.market_cap)}. Peer sizes below load independently; annual-share proxies above remain the basis of the trading multiples.`,'help');
        const peerGrid=add(parent,'div','','reference-grid');
        await Promise.all(doc.source.peer_suggestions.map(async peer=>{
          const card=add(peerGrid,'article',`${peer.ticker} · loading current market cap…`,'reference-card');
          try {
            const response=await fetch(`/api/references/${encodeURIComponent(peer.ticker)}`,{signal:request.signal});
            const packet=await response.json();if(!response.ok)throw new Error();
            if(token!==generation)return;
            card.textContent=Number.isFinite(packet.market_cap)&&packet.market_cap>0?`${peer.ticker}: ${compactUsd(packet.market_cap)} · ${(packet.market_cap/data.market_cap).toFixed(2)}× target current market cap · retrieved ${packet.retrieved_at}`:`${peer.ticker}: current reported market cap unavailable; review the dated annual-share proxy.`;
          } catch(_) {if(token===generation)card.textContent=`${peer.ticker}: current reported market cap unavailable; review the dated annual-share proxy.`;}
        }));
      }
      if(token!==generation)return;
      const line=add(parent,'p',`Retrieved ${data.retrieved_at}. `,'help');
      const link=add(line,'a',data.source);link.href=data.source_url;link.rel='noreferrer';link.target='_blank';
    } catch(error) {
      if(error.name!=='AbortError'&&token===generation)status.textContent=`Analyst references unavailable: ${error.message} Your valuation can still proceed.`;
    }
  }
  function refresh() {
    let doc;
    try {doc=JSON.parse(form ? form.elements.base_document.value : result.dataset.document);}catch(_){return;}
    if(request)request.abort();const token=++generation;
    if(form)lock(doc);
    if(document.body.classList.contains("embedded-editor"))return;
    const parent=form?box:result;if(!parent)return;
    parent.replaceChildren();parent.hidden=false;
    if(form) {
      add(parent,'p','Decision references','eyebrow');
      if(form.dataset.method==='ddm') {
        history(parent,doc.source?.dividend_growth_reference,'Historical common dividends paid');
        add(parent,'p','Growth uses total annual common cash dividends, matching this DDM’s forecast basis. Repurchases and preferred dividends are excluded; total-payout growth differs from dividend-per-share growth.','help');
        history(parent,doc.source?.dividend_per_share_growth_reference,'Historical dividend-per-share proxy',usd);
        add(parent,'p','Per-share proxy = common dividends paid / annual diluted weighted-average shares. This is not split-adjusted declared dividend per share.','help');
      } else history(parent,doc.source?.revenue_growth_reference,'Historical revenue growth');
      for(const peer of doc.source?.peer_suggestions||[]) {
        const card=add(parent,'article','','reference-card');
        add(card,'strong',`${peer.ticker} · ${peer.name}`);
        add(card,'span',`${peer.fit_label} · ${peer.industry} · ${peer.market_cap_ratio!=null?peer.market_cap_ratio.toFixed(2)+'× target market-equity size':'Size unavailable'}`);
        add(card,'span',`Products / segments: ${(peer.segments||[]).join(', ')}. Shared: ${(peer.shared_products_segments||[]).join(', ')||'Unverified'}.`);
        if(peer.caveats?.length)add(card,'span',peer.caveats.join(' '));
      }
      if(doc.source?.peer_suggestions?.length)add(parent,'p',doc.source.peer_suggestions[0].source+' Suggestions are ranked by industry, shared products and size; review competitive fit before including a peer.','help');
    } else {
      add(parent,'p','Price comparison','eyebrow');add(parent,'h2','Your valuation, market and analyst consensus');
      add(parent,'p',`Model 12-month target: ${usd(Number(result.dataset.target))} · current loaded market price: ${usd(doc.market.price)} (${doc.market.price_as_of}) · ${pct(Number(result.dataset.target)/doc.market.price-1)} implied price upside / downside.`);
      add(parent,'p','The intrinsic value today and 12-month model scenario have different horizons. This comparison uses the model’s 12-month scenario and excludes dividends. Market price may be delayed.','help');
    }
    if(form?.dataset.method!=='ddm')references(doc,parent,!form,token);
  }
  document.addEventListener('financials-loaded',refresh);
  document.addEventListener('DOMContentLoaded',()=>{if(form||result)refresh();});
})();
