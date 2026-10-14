/* EV ChargeOps — frontend React sem transpile, consumindo somente rotas FastAPI.
   Os dados exibidos são provenientes da API, nunca cifras de fatura fixadas na UI.
   React 16 UMD é usado para permitir demonstrar o protótipo sem npm. */
(function () {
  'use strict';
  const h = React.createElement;
  const API = (location.hostname === 'localhost' ? 'http://localhost:8000' : 'http://127.0.0.1:8000');
  const brl = n => Number(n || 0).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
  const num = (n, digits=2) => Number(n || 0).toLocaleString('pt-BR', {minimumFractionDigits: digits, maximumFractionDigits: digits});
  const shortDate = val => { try {return new Intl.DateTimeFormat('pt-BR', {timeZone:'America/Sao_Paulo',day:'2-digit',month:'2-digit',year:'numeric'}).format(new Date(val));} catch (_) {return val || '—';} };
  const dateTime = val => { try {return new Intl.DateTimeFormat('pt-BR', {timeZone:'America/Sao_Paulo',day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}).format(new Date(val));} catch (_) {return val || '—';} };
  const sum = (arr, prop) => arr.reduce((a,b) => a + Number(b[prop] || 0), 0);
  const baseForm = () => ({ usuario_id:'U001', carregador_id:'C001', inicio:'2026-10-14T14:00', fim:'2026-10-14T16:00', energia_kwh:'10.000', estado:'concluida', validado:true });
  const cls = (...s) => s.filter(Boolean).join(' ');
  const icon = (name) => {
    const paths = {
      dashboard: h('path',{d:'M3 3h8v8H3z M13 3h8v5h-8z M13 10h8v11h-8z M3 13h8v8H3z'}),
      sessions: h('path',{d:'M7 2v4M17 2v4M3 10h18 M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z'}),
      billing: h('path',{d:'M4 2h16v20l-4-2-4 2-4-2-4 2z M8 8h8 M8 12h8 M8 16h5'}),
      ai: h('path',{d:'M8 3a3 3 0 0 0-5 2 3 3 0 0 0-1 5 3 3 0 0 0 1 5 3 3 0 0 0 5 4V3z M16 3a3 3 0 0 1 5 2 3 3 0 0 1 1 5 3 3 0 0 1-1 5 3 3 0 0 1-5 4V3z M8 7h4v10 M16 7h-4 M16 15h-4'}),
      bolt: h('path',{d:'M13 2 4 13h7l-1 9 10-12h-7z'}),
      check: h('path',{d:'M20 6 9 17l-5-5'}),
      refresh: h('path',{d:'M20 11a8 8 0 1 0-2 6 M20 4v7h-7'}),
      arrow: h('path',{d:'M5 12h14m-6-6 6 6-6 6'}),
      alert: h('path',{d:'M12 3 2 21h20L12 3z M12 9v5 M12 18h.01'}),
      plug: h('path',{d:'M7 3v7M17 3v7M6 10h12v3a6 6 0 0 1-12 0zM12 19v3'}),
      chart: h('path',{d:'M3 3v18h18 M7 16l4-5 4 3 5-8'}),
      database: h('path',{d:'M3 6c0-4 18-4 18 0s-18 4-18 0 M3 6v12c0 4 18 4 18 0V6 M3 12c0 4 18 4 18 0'}),
    };
    return h('svg', {viewBox:'0 0 24 24', width:19,height:19,fill:'none',stroke:'currentColor',strokeWidth:1.7,strokeLinecap:'round',strokeLinejoin:'round','aria-hidden':'true'}, paths[name] || paths.bolt);
  };
  const tag = (v, tone) => h('span',{className:cls('tag',tone && `tag-${tone}`)},v);
  const panel = (title, subtitle, child, right) => h('section',{className:'panel'},
    h('div',{className:'panel-heading'},h('div',null,h('h3',null,title), subtitle&&h('p',null,subtitle)),right),child);
  const stat = (label, value, foot, ic, tone) => h('div',{className:'stat-card'},
    h('div',{className:'stat-top'},h('span',null,label),h('span',{className:cls('stat-icon',tone)},icon(ic))),
    h('div',{className:'stat-value'},value),h('div',{className:'stat-foot'},foot));
  const T = ({headers, rows, empty}) => h('div',{className:'table-wrap'},h('table',null,
    h('thead',null,h('tr',null,headers.map((v,i)=>h('th',{key:i},v)))),
    h('tbody',null,rows.length ? rows : h('tr',null,h('td',{colSpan:headers.length,className:'empty'},empty || 'Nenhum registro disponível.')))));
  function BarChart(props) {
    const data = props.data || [];
    const max = Math.max(...data.map(x=>Number(x.value || 0)),1);
    return h('div',{className:'chart-wrap'},
      h('div',{className:'chart-grid'},h('span',null,num(max,0)+' kWh'),h('span',null,num(max/2,0)+' kWh'),h('span',null,'0 kWh')),
      h('div',{className:'bar-chart'},data.map((x,i)=>h('div',{key:i,className:'bar-column',title:x.label+': '+num(x.value,2)+' kWh'},
         h('div',{className:cls('bar',x.highlight&&'bar-highlight'),style:{height:Math.max(4,Number(x.value||0)/max*100)+'%'}}),
         h('span',{className:'bar-label'},x.short || x.label)))))
  }
  const nav = [{id:'overview',name:'Visão geral',ico:'dashboard'},{id:'sessions',name:'Sessões de recarga',ico:'sessions'},{id:'billing',name:'Rateio e faturas',ico:'billing'},{id:'ai',name:'Inteligência artificial',ico:'ai'}];
  class App extends React.Component {
    constructor(props) {
      super(props);
      this.state={section:'overview',period:'2026-10',data:null,loading:true,submitting:false,error:'',notice:'',form:baseForm()};
      this.reload=this.reload.bind(this); this.changeSection=this.changeSection.bind(this); this.submit=this.submit.bind(this);
    }
    componentDidMount() { this.reload(); }
    async reload(period=this.state.period) {
      this.setState({loading:true,error:'',notice:''});
      try {
        const paths=['/api/health','/api/users','/api/chargers','/api/sessions','/api/invoices?period='+encodeURIComponent(period),'/api/ai/forecast','/api/ai/anomalies','/api/ai/recommendations','/api/config'];
        const res=await Promise.all(paths.map(x=>fetch(API+x)));
        for (const r of res) if(!r.ok) throw new Error('Resposta da API: HTTP '+r.status);
        const arr=await Promise.all(res.map(x=>x.json()));
        this.setState({loading:false,data:{health:arr[0],users:arr[1],chargers:arr[2],sessions:arr[3],invoices:arr[4],forecast:arr[5],anomalies:arr[6],recommendations:arr[7],config:arr[8]},period});
      } catch(e){this.setState({loading:false,error:'Falha ao consultar o backend. Inicie o FastAPI na porta 8000. Detalhe: '+e.message});}
    }
    changeSection(section) {this.setState({section,notice:'',error:''});}
    setForm(k,v) {this.setState(s=>({form:{...s.form,[k]:v}}));}
    async submit(e) {
      e.preventDefault(); this.setState({submitting:true,error:'',notice:''});
      const f=this.state.form;
      const id='WEB-'+Date.now().toString(36).toUpperCase();
      const body={id,usuario_id:f.usuario_id,carregador_id:f.carregador_id,inicio:f.inicio+':00-03:00',fim:f.fim+':00-03:00',energia_kwh:f.energia_kwh,estado:f.estado,origem:'manual',validado:f.estado!=='falha_comunicacao'};
      try {
        const r=await fetch(API+'/api/sessions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
        const data=await r.json();
        if(!r.ok) {const d=typeof data.detail==='string' ? data.detail : JSON.stringify(data.detail||data);throw new Error(d);}
        await this.reload(this.state.period);
        this.setState({submitting:false,notice:'Sessão '+id+' cadastrada. Rateio e IA atualizados a partir da mesma base.',form:{...baseForm(),inicio:f.inicio,fim:f.fim}});
      } catch(e){this.setState({submitting:false,error:'Não foi possível cadastrar: '+e.message});}
    }
    renderHeader(){const {section,period,loading,data}=this.state;const title=nav.find(x=>x.id===section)?.name||'Visão geral';return h('div',{className:'header'},
      h('div',null,h('div',{className:'breadcrumbs'},'EV ChargeOps',h('span',null,'/'),title),h('h1',null,title),h('p',{className:'header-sub'},'Gestão inteligente e transparente de recargas compartilhadas')),
      h('div',{className:'header-actions'},h('label',{className:'period-select'},'PERÍODO',h('input',{type:'month','aria-label':'Período de referência',value:period,onChange:e=>this.reload(e.target.value)})),
      h('button',{className:'btn btn-light',onClick:()=>this.reload(),disabled:loading},icon('refresh'),' Atualizar')));
    }
    renderSidebar(){return h('aside',{className:'sidebar'},
      h('div',{className:'brand'},h('div',{className:'brand-mark'},icon('bolt')),h('div',null,h('strong',null,'EV ChargeOps'),h('small',null,'GOODWE × FIAP'))),
      h('div',{className:'side-divider'}),h('div',{className:'side-label'},'MENU PRINCIPAL'),
      h('nav',{'aria-label':'Menu principal'},nav.map(n=>h('button',{key:n.id,className:cls('nav-item',this.state.section===n.id&&'active'),onClick:()=>this.changeSection(n.id)},icon(n.ico),n.name))),
      h('div',{className:'sidebar-bottom'},h('div',{className:'demo-label'},h('span',{className:'online-dot'}),'MODO DEMONSTRAÇÃO'),h('p',null,'Dados fictícios. Sem conexão física ao carregador GoodWe.'),h('div',{className:'side-credit'},'ENTERPRISE CHALLENGE 2026',h('br'),'SPRINT 02 · GRUPO 20')));
    }
    overview(d){
      const s=d.sessions.filter(x=>String(x.inicio).slice(0,7)===this.state.period || shortDate(x.inicio).slice(3,10)===(this.state.period.slice(5)+'/'+this.state.period.slice(0,4))); // mês local considerado nas faturas
      const totals={kwh:sum(d.invoices,'energia_kwh'),price:sum(d.invoices,'total'),pending:sum(d.invoices,'sessoes_pendentes'),charged:sum(d.invoices,'sessoes_cobradas')};
      const top=d.invoices.filter(x=>Number(x.energia_kwh)>0).sort((a,b)=>Number(b.energia_kwh)-Number(a.energia_kwh));
      const ds=(d.forecast.previsoes||[]).map(x=>({label:x.data,short:x.data.slice(8,10)+'/'+x.data.slice(5,7),value:x.kwh_previstos,highlight:x.acima_limiar_historico}));
      const rec=d.recommendations.recomendacoes||[];
      return h('div',null,
        h('div',{className:'notice-banner'},h('div',{className:'banner-icon'},icon('plug')),h('div',null,h('strong',null,'Operação compartilhada, decisões baseadas em dados.'),h('p',null,'Carregador GoodWe HCA G2 como referência. Sessões e telemetria são simuladas.')),
          h('button',{className:'btn btn-banner',onClick:()=>this.changeSection('sessions')},'Nova sessão ',icon('arrow'))),
        h('div',{className:'stats-grid'},stat('Consumo faturável',num(totals.kwh)+' kWh','Referente a '+this.state.period, 'bolt','mint'),stat('Receita simulada',brl(totals.price),'Tarifa + manutenção única','billing','blue'),stat('Sessões cobradas',String(totals.charged),'Registros validados no mês','sessions','purple'),stat('Pendências',String(totals.pending),'Não incluídas na cobrança','alert','orange')),
        h('div',{className:'two-cols'},panel('Previsão de demanda','Estimativa para os 7 dias seguintes ao último registro válido',ds.length?h(BarChart,{data:ds}):h('p',{className:'empty'},d.forecast.mensagem||'Sem dados suficientes'),tag('Random Forest','mint')),
          panel('Consumo por usuário','Ranking do mês selecionado',h('div',{className:'rank-list'},top.length?top.map((x,i)=>h('div',{className:'rank-item',key:x.usuario_id},
            h('span',{className:'rank-avatar'},'0'+(i+1)),h('div',{className:'rank-name'},h('strong',null,x.usuario_nome),h('small',null,x.sessoes_cobradas+' sessões')),
            h('strong',null,num(x.energia_kwh)+' kWh'))):h('p',{className:'empty'},'Nenhum consumo faturável.')),tag('kWh medido','plain'))),
        panel('Inteligência operacional','Recomendações baseadas nos modelos aplicados ao mesmo banco de sessões',
          h('div',{className:'rec-list'},rec.slice(0,3).map((r,i)=>h('div',{key:i,className:'recommend'},h('div',{className:'rec-head'},tag(r.prioridade,'tag-'+(r.prioridade==='alta'?'warn':'soft')),h('strong',null,r.mensagem)),h('p',null,r.evidencia)))),
          h('button',{className:'inline-link',onClick:()=>this.changeSection('ai')},'Ver análise completa →')));
    }
    sessions(d){const sorted=d.sessions.slice().sort((a,b)=>new Date(b.inicio)-new Date(a.inicio));const f=this.state.form;const ff=(name,field)=>h('label',{className:'field'},h('span',null,name),field);
      const inp=(key,type,opts={})=>h('input',{type:type||'text',value:f[key],required:true,step:opts.step,min:opts.min,onChange:e=>this.setForm(key,e.target.value)});
      const sel=(key,entries)=>h('select',{value:f[key],onChange:e=>this.setForm(key,e.target.value)},entries.map(x=>h('option',{value:x[0],key:x[0]},x[1])));
      return h('div',{className:'two-cols sessions-layout'},panel('Cadastrar nova sessão','Os registros alimentam simultaneamente o rateio e a IA.',
        h('form',{className:'session-form',onSubmit:this.submit},
          ff('Usuário',sel('usuario_id',d.users.map(x=>[x.id,x.nome+' ('+x.id+')']))),
          ff('Carregador',sel('carregador_id',d.chargers.map(x=>[x.id,x.modelo+' ('+x.id+')']))),
          h('div',{className:'form-row'},ff('Início (horário de São Paulo)',inp('inicio','datetime-local')),ff('Fim (horário de São Paulo)',inp('fim','datetime-local'))),
          h('div',{className:'form-row'},ff('Energia medida (kWh)',inp('energia_kwh','number',{step:'0.001',min:'0'})),ff('Estado',sel('estado',[['concluida','Concluída'],['interrompida','Interrompida'],['falha_comunicacao','Falha de comunicação']]))),
          h('p',{className:'hint'},'Falhas ficam pendentes, sem entrar na fatura. Horários sobrepostos no mesmo carregador são rejeitados.'),
          h('button',{className:'btn btn-primary submit',type:'submit',disabled:this.state.submitting},this.state.submitting?'Salvando...':'Registrar sessão',icon('arrow')))),
        panel('Sessões registradas','Histórico exibido diretamente do backend ('+sorted.length+' registros)',
          h(T,{headers:['ID','Usuário','Início (SP)','kWh','Status'],rows:sorted.slice(0,30).map(x=>h('tr',{key:x.id},h('td',{className:'mono'},x.id),h('td',null,x.usuario_id),h('td',null,dateTime(x.inicio)),h('td',{className:'num'},num(x.energia_kwh,3)),h('td',null,tag(x.validado?(x.estado==='concluida'?'Concluída':'Interrompida'):'Pendente',x.validado?'mint':'warn'))))}),
          h('p',{className:'hint'},'Exibindo até 30 sessões mais recentes. Histórico completo disponível na API.')));
    }
    billing(d){const total=sum(d.invoices,'total');return h('div',null,
      h('div',{className:'stats-grid two'},stat('Energia total',num(sum(d.invoices,'energia_kwh'))+' kWh','Somente sessões validadas','bolt','mint'),stat('Faturamento ilustrativo',brl(total),'Sem cobrança real','billing','blue')),
      panel('Faturas individuais','Modelo: energia medida × '+brl(d.config.tarifa_kwh)+'/kWh + '+brl(d.config.manutencao_mensal)+' por usuário com consumo faturável. Tarifas consultadas na API.',
       h(T,{headers:['Usuário','Sessões','Consumo','Energia (R$)','Manutenção','Total','Situação'],rows:d.invoices.map(x=>h('tr',{key:x.usuario_id},h('td',null,h('strong',null,x.usuario_nome),h('small',{className:'cell-sub'},x.usuario_id)),h('td',null,x.sessoes_cobradas),h('td',{className:'num'},num(x.energia_kwh,3)+' kWh'),h('td',{className:'num'},brl(x.custo_energia)),h('td',{className:'num'},brl(x.taxa_manutencao)),h('td',{className:'num total'},brl(x.total)),h('td',null,tag(x.sessoes_pendentes?'Revisão pendente':x.sessoes_cobradas?'Calculada':'Sem consumo',x.sessoes_pendentes?'warn':'mint'))))})),
      h('div',{className:'info-strip'},icon('alert'),' Relatório demonstrativo: não gera faturas fiscais, pagamentos ou acionamento físico de equipamentos.'));
    }
    ai(d){const f=d.forecast,a=d.anomalies,r=d.recommendations;const ds=(f.previsoes||[]).map(x=>({label:x.data,short:x.data.slice(8,10)+'/'+x.data.slice(5,7),value:x.kwh_previstos,highlight:x.acima_limiar_historico}));
      return h('div',null,h('div',{className:'stats-grid three'},stat('Sessões analisadas',String(a.sessoes_analisadas),'Registros validados','database','blue'),stat('Anomalias detectadas',String(a.total_anomalias),'Marcadores estatísticos','alert','orange'),stat('MAE Random Forest',f.metricas?num(f.metricas.mae_modelo_kwh,3)+' kWh':'—','Comparação cronológica','chart','mint')),
        h('div',{className:'two-cols'},panel('Previsão diária','RandomForestRegressor · 7 dias futuros',
          h('div',null,f.status==='ok'?h(BarChart,{data:ds}):h('p',{className:'empty'},f.mensagem),
          f.metricas&&h('div',{className:'metric-note'},h('span',null,'MAE do modelo: ',h('strong',null,num(f.metricas.mae_modelo_kwh,3)+' kWh')),h('span',null,'MAE da média móvel: ',h('strong',null,num(f.metricas.mae_baseline_media_7d_kwh,3)+' kWh')),tag(f.metricas.supera_baseline?'Superou baseline':'Não superou baseline',f.metricas.supera_baseline?'mint':'warn'))),tag(f.status==='ok'?'Modelo executado':'Aguardando dados','soft')),
         panel('Anomalias identificadas','Isolation Forest · sessões atípicas não implicam fraude',
           h(T,{headers:['Sessão','Consumo','Score','Indícios'],rows:(a.anomalias||[]).slice(0,7).map(x=>h('tr',{key:x.sessao_id},h('td',{className:'mono'},x.sessao_id),h('td',null,num(x.energia_kwh,1)+' kWh'),h('td',{className:'num'},num(x.score,4)),h('td',null,x.indicadores_descritivos.join('; '))))}),tag(a.status==='ok'?'Modelo executado':'Aguardando dados','soft'))),
        panel('Recomendações operacionais','Resultados de IA + regras transparentes · revisão humana obrigatória',
           h('div',{className:'rec-list'},(r.recomendacoes||[]).map((x,i)=>h('div',{key:i,className:'recommend'},h('div',{className:'rec-head'},tag(x.prioridade,x.prioridade==='alta'?'warn':'soft'),h('strong',null,x.mensagem)),h('p',null,x.evidencia)))),tag(r.status==='ok'?'Integrado à API':'Parcial','plain')),
        h('div',{className:'info-strip'},icon('alert'),' Modelos treinados com dados sintéticos. Resultados indicativos; sem medição real, inferência de fraude ou ação automática.'));
    }
    render(){const {data,loading,error,notice,section}=this.state;return h('div',{className:'app-shell'},this.renderSidebar(),h('main',{className:'main-content'},
      this.renderHeader(),
      error&&h('div',{className:'message error','role':'alert'},icon('alert'),error),
      notice&&h('div',{className:'message success','role':'status'},icon('check'),notice),
      loading?h('div',{className:'loading-panel'},h('div',{className:'loading-ring'}),'Consultando sessões e treinando modelos de IA...'):
      data&&(section==='overview'?this.overview(data):section==='sessions'?this.sessions(data):section==='billing'?this.billing(data):this.ai(data)),
      h('footer',null,'FIAP · GOODWE · GRUPO 20',h('span',null,'EV ChargeOps 2026 | Protótipo acadêmico · Dados simulados'))));}
  }
  ReactDOM.render(h(App),document.getElementById('root'));
})();
