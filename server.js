const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Servir arquivos estáticos
app.use(express.static(path.join(__dirname, '../public')));

// API Routes para Emails (futuramente com SendGrid)
app.post('/api/email/send', (req, res) => {
  const { to, subject, content } = req.body;
  
  // Simulado por enquanto - integrará com SendGrid
  console.log(`Email enviado para: ${to}`);
  console.log(`Assunto: ${subject}`);
  
  res.json({ 
    success: true, 
    message: 'Email preparado para envio',
    timestamp: new Date().toISOString()
  });
});

// API Routes para SMS (futuramente com Twilio)
app.post('/api/sms/send', (req, res) => {
  const { phone, message } = req.body;
  
  // Simulado por enquanto - integrará com Twilio
  console.log(`SMS enviado para: ${phone}`);
  console.log(`Mensagem: ${message}`);
  
  res.json({ 
    success: true, 
    message: 'SMS preparado para envio',
    timestamp: new Date().toISOString()
  });
});

// API Routes para Exportação
app.get('/api/export/csv', (req, res) => {
  res.setHeader('Content-Type', 'text/csv');
  res.setHeader('Content-Disposition', 'attachment; filename="pacientes.csv"');
  
  const csvContent = 'Nome,CPF,Telefone,Email,Secretária,Status\n';
  res.send(csvContent);
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'production'
  });
});

// Rota principal - Serve a aplicação React
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/index.html'));
});

// Fallback para qualquer rota não definida
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/index.html'));
});

// Tratamento de erros
app.use((err, req, res, next) => {
  console.error('Erro:', err);
  res.status(500).json({ 
    error: 'Erro interno do servidor',
    message: err.message 
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`✅ Servidor rodando em porta ${PORT}`);
  console.log(`🌐 Acesse: http://localhost:${PORT}`);
});

module.exports = app;
