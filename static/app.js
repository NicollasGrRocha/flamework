const API_BASE = '' // mesma origem

async function sendVerificationCode() {
  const msg = document.getElementById('verification-message');
  msg.textContent = 'Enviando código...';
  msg.style.color = 'blue';
  try {
    const res = await fetch(API_BASE + '/send-code', {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Erro ao enviar código');
    msg.textContent = 'Código enviado! Verifique seu WhatsApp.';
    msg.style.color = 'green';
  } catch (err) {
    msg.textContent = 'Erro ao enviar código: ' + err.message;
    msg.style.color = 'red';
    console.error(err);
  }
}

async function verifyCode(code) {
  const msg = document.getElementById('verification-message');
  msg.textContent = 'Verificando...';
  msg.style.color = 'blue';
  try {
    const res = await fetch(API_BASE + '/verify-code', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ code })
    });
    if (!res.ok) throw new Error('Código inválido');
    msg.textContent = 'Código verificado com sucesso!';
    msg.style.color = 'green';
  } catch (err) {
    msg.textContent = 'Erro na verificação: ' + err.message;
    msg.style.color = 'red';
    console.error(err);
  }
}

// Event listeners para verificação
document.getElementById('send-code').addEventListener('click', () => {
  sendVerificationCode();
});

document.getElementById('verify-code').addEventListener('click', () => {
  const code = document.getElementById('verification-code').value;
  if (!code) {
    const msg = document.getElementById('verification-message');
    msg.textContent = 'Por favor, digite o código recebido';
    msg.style.color = 'red';
    return;
  }
  verifyCode(code);
});

async function fetchProducts(){
  const res = await fetch(API_BASE + '/produto');
  if(!res.ok) throw new Error('Erro ao buscar produtos');
  return res.json();
}

function productCard(prod){
  const div = document.createElement('div');
  div.className = 'product';
  const img = document.createElement('img');
  // se houver imagem, usa o path retornado pelo backend; caso contrário, usa um SVG inline simples
  img.src = prod.imagem ? '/' + prod.imagem.replace(/\\/g,'/') : 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200"><rect width="100%" height="100%" fill="%23ECECEC"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="%23999" font-family="Arial, Helvetica, sans-serif" font-size="18">Sem imagem</text></svg>';
  img.alt = prod.nome || '';
  div.appendChild(img);
  const name = document.createElement('div'); name.textContent = prod.nome; div.appendChild(name);
  const price = document.createElement('div'); price.textContent = 'R$ ' + (parseFloat(prod.preco)||0).toFixed(2); div.appendChild(price);
  const qty = document.createElement('div'); qty.textContent = 'Qtd: ' + (prod.quantidade||0); div.appendChild(qty);
  const status = document.createElement('div'); status.textContent = 'Status: ' + (prod.status||''); div.appendChild(status);
  return div;
}

async function renderProducts(){
  const container = document.getElementById('products');
  container.innerHTML = 'Carregando...';
  try{
    const produtos = await fetchProducts();
    if(!Array.isArray(produtos)){
      container.innerHTML = '<i>Nenhum produto encontrado</i>';
      return;
    }
    container.innerHTML = '';
    produtos.forEach(p=> container.appendChild(productCard(p)));
  }catch(err){
    container.innerHTML = '<span style="color:red">Erro ao carregar produtos</span>';
    console.error(err);
  }
}

document.getElementById('refresh').addEventListener('click', e=>{ renderProducts(); });

document.getElementById('product-form').addEventListener('submit', async (ev)=>{
  ev.preventDefault();
  const form = ev.target;
  const fd = new FormData(form);
  const msg = document.getElementById('form-message');
  msg.textContent = 'Enviando...';
  try{
    const res = await fetch(API_BASE + '/produto', { method: 'POST', body: fd });
    if(!res.ok){
      const txt = await res.text();
      msg.style.color = 'red';
      msg.textContent = 'Erro: ' + txt;
      return;
    }
    const data = await res.json();
    msg.style.color = 'green';
    msg.textContent = 'Produto criado com sucesso (id: ' + data.id + ')';
    form.reset();
    renderProducts();
  }catch(err){
    msg.style.color = 'red';
    msg.textContent = 'Erro ao enviar';
    console.error(err);
  }
});

// inicializa
renderProducts();
