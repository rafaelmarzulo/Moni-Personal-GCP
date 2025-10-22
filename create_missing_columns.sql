-- Script SQL para criar todas as colunas faltantes na tabela avaliacoes

-- Novos campos específicos para medidas corporais (caso não existam)
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS peso_kg FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS altura_cm FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS percentual_gordura FLOAT;

-- Circunferências em cm
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS circunferencia_pescoco FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS circunferencia_braco_direito FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS circunferencia_braco_esquerdo FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS circunferencia_antebraco_direito FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS circunferencia_antebraco_esquerdo FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS circunferencia_torax FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS circunferencia_cintura FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS circunferencia_abdome FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS circunferencia_quadril FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS circunferencia_coxa_direita FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS circunferencia_coxa_esquerda FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS circunferencia_panturrilha_direita FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS circunferencia_panturrilha_esquerda FLOAT;

-- Dobras cutâneas em mm
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS dobra_bicipital FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS dobra_tricipital FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS dobra_subescapular FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS dobra_suprailiaca FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS dobra_abdominal FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS dobra_coxa FLOAT;

-- Outros dados (caso não existam)
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS imc FLOAT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS observacoes_medidas TEXT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS faltou_algo TEXT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS gostou_mais_menos TEXT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS meta_agua TEXT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS meta_agua_melhorar TEXT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS alimentacao TEXT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS melhorias TEXT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS outros_melhorias TEXT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS pedido_especial TEXT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS rotina_treino TEXT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS sugestao_geral TEXT;
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();