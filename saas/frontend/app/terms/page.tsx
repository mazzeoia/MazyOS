import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Termos de Serviço — CREATIVE ADS",
};

export default function TermsPage() {
  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "48px 24px", fontFamily: "var(--font-body), sans-serif", color: "#1a1a1a", lineHeight: 1.7 }}>
      <h1 style={{ fontSize: "1.8rem", marginBottom: 8 }}>Termos de Serviço</h1>
      <p style={{ color: "#666", marginBottom: 32 }}>Última atualização: 29 de agosto de 2026</p>

      <p>
        Estes Termos de Serviço (&quot;Termos&quot;) regem o uso da plataforma{" "}
        <strong>CREATIVE ADS</strong> (&quot;Plataforma&quot;), operada pela{" "}
        <strong>Creative Agência Marketing LTDA</strong> (&quot;Creative&quot;, &quot;nós&quot;),
        acessível em <em>ads.creativeagenciamkt.com.br</em>. Ao criar uma conta ou usar a
        Plataforma, você concorda com estes Termos.
      </p>

      <h2>1. O que é a Plataforma</h2>
      <p>
        A CREATIVE ADS é uma ferramenta de gestão e otimização de campanhas de anúncios que,
        mediante autorização do usuário via OAuth do Meta, conecta-se à conta de anúncios do
        Meta Ads para exibir métricas, gerar análises com inteligência artificial e executar
        ações que o usuário autorizar (como pausar ou ativar campanhas).
      </p>

      <h2>2. Conta e elegibilidade</h2>
      <ul>
        <li>Você precisa ter uma conta de anúncios Meta Ads válida e permissão para administrá-la.</li>
        <li>Você é responsável por manter a confidencialidade das suas credenciais de acesso à Plataforma.</li>
        <li>A Plataforma é destinada a uso por empresas e profissionais de marketing, não a consumidores finais.</li>
      </ul>

      <h2>3. Automações e ações na conta de anúncios</h2>
      <p>
        Algumas funcionalidades (como a pausa automática de campanhas por regra) executam ações
        reais na sua conta Meta Ads quando você as ativa explicitamente. Você é responsável por
        configurar essas regras de acordo com o comportamento que deseja e por revisar os
        resultados. A Creative não se responsabiliza por resultados de campanha, gastos ou perda
        de desempenho decorrentes de configurações definidas pelo próprio usuário.
      </p>

      <h2>4. Uso aceitável</h2>
      <p>Ao usar a Plataforma, você concorda em não:</p>
      <ul>
        <li>Usar a Plataforma para fins ilegais ou que violem os Termos e Políticas do Meta.</li>
        <li>Tentar acessar contas, dados ou sistemas de terceiros sem autorização.</li>
        <li>Fazer engenharia reversa, copiar ou revender a Plataforma sem autorização por escrito.</li>
        <li>Sobrecarregar deliberadamente a infraestrutura da Plataforma ou das APIs que ela consome.</li>
      </ul>

      <h2>5. Integração com o Meta</h2>
      <p>
        O uso da Plataforma em conjunto com o Meta Ads está sujeito também às{" "}
        <a href="https://www.facebook.com/policies_center/" style={{ color: "#e85d04" }}>
          Políticas da Plataforma Meta
        </a>{" "}
        e aos Termos de Serviço do Meta Business. Em caso de conflito quanto ao uso de dados
        obtidos via Meta Marketing API, as políticas do Meta prevalecem.
      </p>

      <h2>6. Propriedade intelectual</h2>
      <p>
        A Plataforma, seu código, design e marca pertencem à Creative Agência Marketing LTDA.
        Os dados das suas campanhas e contas de anúncios continuam sendo seus — a Creative apenas
        os processa para fornecer o serviço, conforme descrito na{" "}
        <a href="/privacy" style={{ color: "#e85d04" }}>Política de Privacidade</a>.
      </p>

      <h2>7. Disponibilidade e alterações no serviço</h2>
      <p>
        Fazemos esforços razoáveis para manter a Plataforma disponível, mas não garantimos
        operação ininterrupta. Podemos alterar, suspender ou descontinuar funcionalidades a
        qualquer momento, com aviso prévio quando a mudança afetar significativamente o uso.
      </p>

      <h2>8. Limitação de responsabilidade</h2>
      <p>
        A Plataforma é fornecida &quot;como está&quot;. Na máxima extensão permitida por lei, a
        Creative não se responsabiliza por danos indiretos, lucros cessantes ou perdas
        decorrentes do uso da Plataforma, incluindo resultados de campanhas publicitárias.
      </p>

      <h2>9. Encerramento</h2>
      <p>
        Você pode encerrar sua conta a qualquer momento solicitando a exclusão dos seus dados
        (veja <a href="/data-deletion" style={{ color: "#e85d04" }}>instruções de exclusão de dados</a>).
        Podemos suspender ou encerrar contas que violem estes Termos.
      </p>

      <h2>10. Alterações nestes Termos</h2>
      <p>
        Podemos atualizar estes Termos periodicamente. Alterações significativas serão
        comunicadas por e-mail ou pela Plataforma. O uso continuado após a atualização
        representa aceitação dos novos Termos.
      </p>

      <h2>11. Lei aplicável</h2>
      <p>
        Estes Termos são regidos pelas leis da República Federativa do Brasil. Fica eleito o
        foro da comarca de domicílio da Creative Agência Marketing LTDA para dirimir eventuais
        controvérsias.
      </p>

      <h2>12. Contato</h2>
      <p>
        Creative Agência Marketing LTDA<br />
        E-mail: <strong>contato@creativeagenciamkt.com.br</strong>
      </p>
    </main>
  );
}
