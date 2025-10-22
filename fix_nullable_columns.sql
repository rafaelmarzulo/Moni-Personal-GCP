-- Script SQL para corrigir constraints NOT NULL nas colunas que devem permitir NULL
-- Executar no Supabase para garantir que todas as colunas opcionais permitam valores NULL

-- Remover constraint NOT NULL das colunas de texto (questionário)
ALTER TABLE avaliacoes ALTER COLUMN observacoes_medidas DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN faltou_algo DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN gostou_mais_menos DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN meta_agua DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN meta_agua_melhorar DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN alimentacao DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN melhorias DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN outros_melhorias DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN pedido_especial DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN rotina_treino DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN sugestao_geral DROP NOT NULL;

-- Remover constraint NOT NULL das colunas de medidas físicas
ALTER TABLE avaliacoes ALTER COLUMN peso_kg DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN altura_cm DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN percentual_gordura DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN imc DROP NOT NULL;

-- Remover constraint NOT NULL das circunferências
ALTER TABLE avaliacoes ALTER COLUMN circunferencia_pescoco DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN circunferencia_braco_direito DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN circunferencia_braco_esquerdo DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN circunferencia_antebraco_direito DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN circunferencia_antebraco_esquerdo DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN circunferencia_torax DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN circunferencia_cintura DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN circunferencia_abdome DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN circunferencia_quadril DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN circunferencia_coxa_direita DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN circunferencia_coxa_esquerda DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN circunferencia_panturrilha_direita DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN circunferencia_panturrilha_esquerda DROP NOT NULL;

-- Remover constraint NOT NULL das dobras cutâneas
ALTER TABLE avaliacoes ALTER COLUMN dobra_bicipital DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN dobra_tricipital DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN dobra_subescapular DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN dobra_suprailiaca DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN dobra_abdominal DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN dobra_coxa DROP NOT NULL;

-- Campos antigos de compatibilidade também devem permitir NULL
ALTER TABLE avaliacoes ALTER COLUMN peso DROP NOT NULL;
ALTER TABLE avaliacoes ALTER COLUMN medidas DROP NOT NULL;