<h1>Simulador de Investimentos</h1>
<p>
    Este é um simulador de investimentos desenvolvido como parte do Trabalho de Conclusão de Curso (TCC).
    A aplicação utiliza uma arquitetura monolítica com <strong>Django</strong> no backend e <strong>React</strong> no frontend,
    e os dados são armazenados em um banco de dados <strong>PostgreSQL</strong>.
</p>
<h2>Tecnologias Utilizadas</h2>
<ul>
    <li>Backend: Django</li>
    <li>Frontend: React</li>
    <li>Banco de Dados: PostgreSQL</li>
    <li>Containerização: Docker</li>
</ul>
<h2>Link para Acessar a Aplicação</h2>
<p>
    A aplicação está hospedada na AWS e pode ser acessada pelo seguinte endereço: <br>
    <a href="http://18.223.198.10:8000" target="_blank">http://18.223.198.10:8000</a>
</p>
<h2>Tutorial de Cadastro e Login</h2>

<h2>Como se cadastrar</h2>
<ol>
    <li>Acesse o sistema através da URL: <a href="http://18.223.198.10:8000/account/login/" target="_blank">Página de Login</a>.</li>
    <li>Na página de login, clique no link <strong>"Sign up first"</strong>.</li>
    <li>Na página de cadastro:
        <ul>
            <li>Preencha o campo <strong>Email</strong> com um endereço de e-mail válido.</li>
            <li>Escolha um <strong>Username</strong> (nome de usuário único).</li>
            <li>Defina uma <strong>Password</strong> (senha) que atenda aos requisitos exibidos na página, como no mínimo 8 caracteres.</li>
            <li>Confirme a senha no campo <strong>Password (again)</strong>.</li>
        </ul>
    </li>
    <li>Clique no botão <strong>"Sign Up"</strong>.</li>
    <li>Após o cadastro, uma mensagem será exibida solicitando a verificação do endereço de e-mail.</li>
</ol>

<h2>Como verificar o e-mail</h2>
<ol>
    <li>Acesse o e-mail usado no cadastro e procure pela mensagem enviada pelo sistema (<em>simuladordeinvestimentos</em>).</li>
    <li>Abra o e-mail e clique no link de verificação fornecido.</li>
    <li>Na página aberta, clique no botão <strong>"Confirm"</strong> para concluir a verificação.</li>
    <li>Após a verificação, você será redirecionado para a página principal do sistema.</li>
</ol>

<h2>Como fazer login</h2>
<ol>
    <li>Acesse a página de login: <a href="http://18.223.198.10:8000/account/login/" target="_blank">Página de Login</a>.</li>
    <li>Insira suas credenciais:
        <ul>
            <li><strong>Login:</strong> Seu e-mail ou nome de usuário cadastrado.</li>
            <li><strong>Senha:</strong> A senha definida no cadastro.</li>
        </ul>
    </li>
    <li>Marque a opção <strong>"Remember Me"</strong> se desejar manter-se conectado.</li>
    <li>Clique no botão <strong>"Sign In"</strong>.</li>
    <li>Após o login, você será redirecionado para a página inicial do sistema, onde poderá acessar todas as funcionalidades.</li>
</ol>

<h2>Dicas Importantes</h2>
<ul>
    <li>Certifique-se de usar um e-mail válido para receber o link de confirmação.</li>
    <li>Verifique sua caixa de spam caso o e-mail de verificação não apareça na caixa de entrada.</li>
    <li>Guarde suas credenciais em um local seguro.</li>
</ul>
