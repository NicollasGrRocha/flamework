let cart = [];

// Carrega lista de produtos da API
async function carregarProdutos() {
  try {
    const res = await fetch("/api/products");

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
      const preco = parseFloat(p.Preco);

      li.innerHTML = `
        <span>${p.NomeProduto} - R$${preco.toFixed(2)} (Estoque: ${p.Quantidade})</span>
        <input type="number" min="1" max="${p.Quantidade}" value="1" id="qtd-${p.IdProduto}">
        <button onclick="adicionarAoCarrinho(${p.IdProduto})">Adicionar</button>
      `;
      lista.appendChild(li);
    });
  } catch (error) {
    console.error("Erro ao carregar produtos:", error);
    document.getElementById("products").innerHTML = "<li>Erro ao carregar produtos.</li>";
  }
}

// Adiciona item ao carrinho
function adicionarAoCarrinho(id) {
  const qtdInput = document.getElementById(`qtd-${id}`);

  if (!qtdInput || qtdInput.value < 1) {
    alert("Selecione uma quantidade válida!");
    return;
  }

  const qtd = parseInt(qtdInput.value);
  const item = { IdProduto: id, Quantidade: qtd };
  cart.push(item);
  alert(`Item (ID: ${id}) adicionado ao carrinho! Quantidade: ${qtd}`);
  atualizarCarrinho();
}

// Atualiza exibição do carrinho (opcional - para futuro uso)
function atualizarCarrinho() {
  console.log("Carrinho atualizado:", cart);
}

// Finaliza a compra enviando o carrinho para a API
async function finalizarCompra() {
  if (cart.length === 0) {
    alert("Carrinho vazio!");
    return;
  }

  try {
    const res = await fetch("/api/purchase", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cart })
    });

    const nota = await res.json();

    if (res.status !== 200) {
      alert(nota.error || "Erro desconhecido ao finalizar compra.");
      return;
    }

    // Exibir nota fiscal
    let html = `<h3>Nota Fiscal</h3><p><strong>Data:</strong> ${nota.data}</p><ul>`;
    nota.itens.forEach(i => {
      const subtotal = parseFloat(i.Subtotal);
      html += `<li>${i.NomeProduto} x${i.Quantidade} - R$${subtotal.toFixed(2)}</li>`;
    });
    html += `</ul><p><strong>Total:</strong> R$${nota.total.toFixed(2)}</p>`;
    html += `<button onclick="imprimirNota()">Imprimir Nota</button>`;
    document.getElementById("notaFiscal").innerHTML = html;

    cart = [];
    carregarProdutos();
    carregarHistorico();
  } catch (error) {
    console.error("Erro ao finalizar compra:", error);
    alert("Erro ao finalizar compra");
  }
}

// Imprime a nota fiscal
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

// Carrega histórico de compras do usuário
async function carregarHistorico() {
  try {
    const res = await fetch("/api/history");

    if (!res.ok) {
      console.warn("Histórico indisponível (erro " + res.status + ")");
      return;
    }

    const historico = await res.json();
    const lista = document.getElementById("historico");
    
    if (!lista) return; // Se elemento não existe, ignora
    
    lista.innerHTML = "";

    historico.forEach(h => {
      const li = document.createElement("li");
      li.innerHTML = `
        <strong>${h.data}</strong>
        Total: R$${h.total.toFixed(2)} <br>
        Itens: ${h.itens.map(i => `${i.NomeProduto} x${i.Quantidade}`).join(", ")}
      `;
      lista.appendChild(li);
    });
  } catch (error) {
    console.warn("Erro ao carregar histórico:", error);
  }
}

// Inicializa a página ao carregar
document.addEventListener("DOMContentLoaded", function() {
  carregarProdutos();
  carregarHistorico();
});