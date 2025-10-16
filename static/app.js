let cart = [];

// Funções CRUD

async function carregarProdutos() {
  // A rota /api/products agora deve retornar os dados do MySQL
  const res = await fetch("/api/products");

  // Tratamento de erro básico
  if (!res.ok) {
      document.getElementById("products").innerHTML = "<li>Erro ao carregar produtos.</li>";
      console.error("Erro na API de produtos:", await res.text());
      return;
  }

  const produtos = await res.json();
  const lista = document.getElementById("products");
  lista.innerHTML = "";

  produtos.forEach(p => {
    const li = document.createElement("li");

    // O Preco vem como string do MySQL (DECIMAL), o parseFloat garante a conversão
    const preco = parseFloat(p.Preco);

    li.innerHTML = `
      <span>${p.NomeProduto} - R$${preco.toFixed(2)} (Estoque: ${p.Quantidade})</span>
      <input type="number" min="1" max="${p.Quantidade}" value="1" id="qtd-${p.IdProduto}">
      <button onclick="adicionarAoCarrinho(${p.IdProduto})">Adicionar</button>
      <button class="delete" onclick="deletarProduto(${p.IdProduto})">Excluir</button>
      <button onclick="editarProduto(${p.IdProduto}, '${p.NomeProduto}', ${preco}, ${p.Quantidade})">Editar</button>
    `;
    lista.appendChild(li);
  });
}

function adicionarAoCarrinho(id) {
  const qtdInput = document.getElementById(`qtd-${id}`);

  // Verifica se o elemento existe e se o valor é válido
  if (!qtdInput || qtdInput.value < 1) {
      alert("Selecione uma quantidade válida!");
      return;
  }

  const qtd = parseInt(qtdInput.value);
  const item = { IdProduto: id, Quantidade: qtd };
  cart.push(item);
  alert(`Item (ID: ${id}) adicionado ao carrinho! Quantidade: ${qtd}`);
}


async function finalizarCompra() {
  if (cart.length === 0) {
    alert("Carrinho vazio!");
    return;
  }

  const res = await fetch("/api/purchase", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cart })
  });

  const nota = await res.json();

  // Verifica o erro retornado pela API
  if (res.status !== 200) {
    alert(nota.error || "Erro desconhecido ao finalizar compra.");
    return;
  }

  // Exibir nota fiscal atual
  let html = `<h3>Nota Fiscal</h3><p><strong>Data:</strong> ${nota.data}</p><ul>`;
  nota.itens.forEach(i => {
    // Garante que Subtotal é um número antes de usar toFixed
    const subtotal = parseFloat(i.Subtotal);
    html += `<li>${i.NomeProduto} x${i.Quantidade} - R$${subtotal.toFixed(2)}</li>`;
  });
  html += `</ul><p><strong>Total:</strong> R$${nota.total.toFixed(2)}</p>`;
  html += `<button onclick="imprimirNota()">Imprimir Nota</button>`;
  document.getElementById("notaFiscal").innerHTML = html;

  cart = [];
  carregarProdutos();
  carregarHistorico(); // Tenta atualizar o histórico
}

function imprimirNota() {
  const conteudo = document.getElementById("notaFiscal").innerHTML;
  const janela = window.open("", "_blank", "width=600,height=700");
  janela.document.write(`
    <html>
      <head>
        <title>Nota Fiscal</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; }
          h3 { text-align: center; margin-bottom: 15px; }
          ul { list-style: none; padding: 0; }
          li { margin-bottom: 8px; }
          p { font-size: 1.1rem; }
          strong { color: #2c3e50; }
        </style>
      </head>
      <body>
        ${conteudo}
      </body>
    </html>
  `);
  janela.document.close();
  janela.print();
}


// Manipulador de formulário para adicionar/editar produtos
document.getElementById("productForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("IdProduto").value;
  const produto = {
    NomeProduto: document.getElementById("NomeProduto").value,
    Preco: parseFloat(document.getElementById("Preco").value),
    Quantidade: parseInt(document.getElementById("Quantidade").value)
  };

  if (isNaN(produto.Preco) || isNaN(produto.Quantidade)) {
      alert("Preço e Quantidade devem ser números válidos.");
      return;
  }

  const url = id ? `/api/products/${id}` : "/api/products";
  const method = id ? "PUT" : "POST";

  const res = await fetch(url, {
    method: method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(produto)
  });

  if (res.ok) {
      alert(`Produto ${id ? 'atualizado' : 'adicionado'} com sucesso!`);
  } else {
      alert("Falha ao salvar produto.");
  }


  document.getElementById("IdProduto").value = ''; // Limpa ID oculto
  e.target.reset(); // Limpa formulário
  carregarProdutos();
});

async function deletarProduto(id) {
  if (confirm("Deseja excluir este produto?")) {
    await fetch(`/api/products/${id}`, { method: "DELETE" });
    carregarProdutos();
  }
}

function editarProduto(id, nome, preco, quantidade) {
  document.getElementById("IdProduto").value = id;
  document.getElementById("NomeProduto").value = nome;
  document.getElementById("Preco").value = preco;
  document.getElementById("Quantidade").value = quantidade;
}

// Funções de Histórico (Requer a rota /api/history no Flask)
async function carregarHistorico() {
  // ATENÇÃO: Se você não adicionou a rota /api/history no app.py,
  // esta função causará um erro 404.
  try {
      const res = await fetch("/api/history");

      // Se a rota não existir (404), apenas ignora a listagem do histórico
      if (!res.ok) return;

      const historico = await res.json();
      const lista = document.getElementById("historico");
      lista.innerHTML = "";

      historico.forEach(h => {
        // Isso assume que o objeto 'h' contém 'data', 'total', e 'itens'
        const li = document.createElement("li");
        li.innerHTML = `
          <strong>${h.data}</strong>
          Total: R$${h.total.toFixed(2)} <br>
          Itens: ${h.itens.map(i => `${i.NomeProduto} x${i.Quantidade}`).join(", ")}
        `;
        lista.appendChild(li);
      });
  } catch (e) {
      console.warn("Rota /api/history indisponível ou erro ao carregar histórico.");
  }
}

// Inicia o carregamento de dados ao abrir a página
carregarProdutos();
// Inicia o carregamento do histórico
carregarHistorico();