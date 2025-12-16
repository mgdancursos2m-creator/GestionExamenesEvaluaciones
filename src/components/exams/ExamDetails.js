import React from 'react';
import { Card, Typography, Divider, List, Tag } from 'antd';
import { CalendarOutlined, UserOutlined, FileTextOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

const ExamDetails = ({ exam }) => {
  const getTypeColor = (type) => {
    const types = {
      'Encuesta': 'blue',
      'Examen': 'green',
      'Quiz': 'orange'
    };
    return types[type] || 'default';
  };

  return (
    <div style={{ padding: '20px' }}>
      <Card>
        {/* Header con información principal */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <Title level={2}>{exam.title || 'Sin título'}</Title>
              <Tag color={getTypeColor(exam.type)} style={{ fontSize: '14px', padding: '4px 8px' }}>
                {exam.type}
              </Tag>
            </div>
          </div>

          <Divider />

          {/* Información del curso e instructor */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
            <div>
              <Text strong><FileTextOutlined /> Curso:</Text>
              <Paragraph style={{ margin: '4px 0' }}>{exam.course}</Paragraph>
            </div>
            <div>
              <Text strong><UserOutlined /> Instructor:</Text>
              <Paragraph style={{ margin: '4px 0' }}>{exam.instructor}</Paragraph>
            </div>
            <div>
              <Text strong><CalendarOutlined /> Fecha Creación:</Text>
              <Paragraph style={{ margin: '4px 0' }}>
                {new Date(exam.creationDate).toLocaleDateString('es-ES', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </Paragraph>
            </div>
          </div>
        </div>

        {/* Lista de preguntas */}
        <Title level={4}>Preguntas ({exam.questions?.length || 0})</Title>
        <List
          itemLayout="vertical"
          dataSource={exam.questions || []}
          renderItem={(question, index) => (
            <List.Item>
              <Card 
                size="small" 
                style={{ width: '100%' }}
                title={
                  <Text strong>
                    Pregunta {index + 1}: {question.text}
                  </Text>
                }
                extra={
                  <Tag color={question.type === 'Respuesta abierta' ? 'green' : 'blue'}>
                    {question.type}
                  </Tag>
                }
              >
                {question.options && question.options.length > 0 && (
                  <div>
                    <Text strong>Opciones:</Text>
                    <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                      {question.options.map((option, optIndex) => (
                        <li key={optIndex}>{option}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </Card>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default ExamDetails;