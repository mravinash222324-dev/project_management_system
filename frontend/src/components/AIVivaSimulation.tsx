import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Button,
  Text,
  Spinner,
  Center,
  useToast,
  Container,
  Textarea,
  Progress,
  Flex,
} from '@chakra-ui/react';
import { motion } from 'framer-motion';
import { RefreshCw, Zap } from 'lucide-react';

// Motion components
const MotionBox = motion(Box);

// Animation variants
const mainContainerVariants = {
  hidden: { opacity: 0, scale: 0.98 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } },
};

const contentVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } },
};

interface EvaluationResult {
  score: string;
  feedback: string;
}

const AIVivaSimulation: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const projectSubmissionId = projectId ? parseInt(projectId) : null;

  const [questions, setQuestions] = useState<string[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(true);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [error, setError] = useState('');
  const [projectProgress, setProjectProgress] = useState(0);

  const navigate = useNavigate();
  const toast = useToast();

  useEffect(() => {
    const fetchAndGenerate = async () => {
      if (!projectSubmissionId) {
        setError('Project ID is missing from the URL.');
        setIsLoadingQuestions(false);
        return;
      }

      setIsLoadingQuestions(true);
      setError('');
      setEvaluation(null);

      try {
        const token = localStorage.getItem('accessToken');
        if (!token) {
          navigate('/');
          return;
        }

        const progressResponse = await axios.get(`http://127.0.0.1:8000/projects/progress/${projectSubmissionId}/`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setProjectProgress(progressResponse.data.progress_percentage || 0);

        const response = await axios.post('http://127.0.0.1:8000/ai/viva/', {
          project_id: projectSubmissionId,
          progress_percentage: progressResponse.data.progress_percentage || 0,
        }, {
          headers: { Authorization: `Bearer ${token}` },
        });

        setQuestions(response.data.questions || []);
        setCurrentQuestionIndex(0);
        setCurrentAnswer('');
      } catch (err) {
        console.error(err);
        toast({
          title: 'Simulation Error',
          description: 'Failed to generate questions. The project might not be approved yet.',
          status: 'error',
          duration: 5000,
          isClosable: true,
          position: 'top',
        });
        setError('Failed to generate questions for this project.');
      } finally {
        setIsLoadingQuestions(false);
      }
    };

    fetchAndGenerate();
  }, [projectSubmissionId, navigate, toast]);

  const handleEvaluateAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentAnswer.trim() || !projectSubmissionId) return;

    setIsEvaluating(true);
    setError('');
    try {
      const token = localStorage.getItem('accessToken');
      const response = await axios.post('http://127.0.0.1:8000/ai/viva/evaluate/', {
        project_id: projectSubmissionId,
        question: questions[currentQuestionIndex],
        answer: currentAnswer,
      }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setEvaluation(response.data);
    } catch (err) {
      console.error(err);
      toast({
        title: 'Evaluation Failed',
        description: 'The AI could not process your answer. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
        position: 'top',
      });
      setError('Failed to evaluate the answer.');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setEvaluation(null);
      setCurrentAnswer('');
    }
  };

  const currentQuestion = questions[currentQuestionIndex];
  const isLastQuestion = currentQuestionIndex >= questions.length - 1;

  // --- Main Render ---
  return (
    <Flex
      w="100%"
      minH="100vh"
      overflowY="auto"
      position="relative"
      justify="center"
      align="center"
      bgGradient="linear(to-bl, #060B26, #0A042A)"
      color="white"
      sx={{
        '&::-webkit-scrollbar': { display: 'none' },
        'scrollbarWidth': 'none',
        '-ms-overflow-style': 'none',
      }}
    >
      {/* Background Glows */}
      <MotionBox position="fixed" top="0" left="0" w="72" h="72" rounded="full" bgGradient="radial(cyan.600, transparent)" filter="blur(180px)" opacity={0.25} />
      <MotionBox position="fixed" bottom="0" right="0" w="80" h="80" rounded="full" bgGradient="radial(blue.600, transparent)" filter="blur(180px)" opacity={0.25} />

      <Container maxW="4xl" zIndex={2} py={{ base: 8, md: 12 }}>
        <MotionBox
          variants={mainContainerVariants}
          initial="hidden"
          animate="visible"
          bg="rgba(10, 15, 40, 0.6)"
          border="1px solid rgba(255, 255, 255, 0.1)"
          borderRadius="3xl"
          boxShadow="0 0 80px rgba(0, 255, 255, 0.1)"
          backdropFilter="blur(20px)"
          p={{ base: 6, md: 10 }}
        >
          {/* Header */}
          <HStack justifyContent="space-between" align="center" borderBottom="1px solid" borderColor="rgba(255,255,255,0.2)" pb={4} mb={6}>
            <Heading as="h1" size="lg" bgGradient="linear(to-r, cyan.400, blue.400)" bgClip="text">
              AI Viva Simulation
            </Heading>
            <Text color="cyan.300" fontWeight="bold" fontSize="sm">
              Project ID: {projectSubmissionId}
            </Text>
          </HStack>

          {/* Progress Bar */}
          <VStack align="stretch" spacing={2} mb={8}>
            <Text fontSize="sm" color="gray.300">
              Simulation based on **{projectProgress}%** project progress.
            </Text>
            <Progress value={projectProgress} size="sm" colorScheme="cyan" bg="rgba(255,255,255,0.1)" borderRadius="full" />
          </VStack>

          {/* Loading State */}
          {isLoadingQuestions && (
            <Center py={20} flexDirection="column">
              <Spinner size="xl" color="cyan.400" thickness="4px" />
              <Text mt={4} color="gray.300">Generating AI questions...</Text>
            </Center>
          )}

          {/* Error State */}
          {error && !isLoadingQuestions && (
            <Center py={20} flexDirection="column">
                <Text fontSize="xl" color="red.400">{error}</Text>
                <Button mt={4} variant="outline" colorScheme="cyan" onClick={() => navigate(-1)}>Go Back</Button>
            </Center>
          )}

          {/* Main Content */}
          {!isLoadingQuestions && questions.length > 0 && (
            <VStack spacing={6} align="stretch">
              {/* Question Box */}
              <MotionBox key={currentQuestionIndex} variants={contentVariants} initial="hidden" animate="visible">
                <VStack
                  bg="rgba(0, 255, 255, 0.05)"
                  p={6}
                  borderRadius="xl"
                  border="1px solid"
                  borderColor="rgba(0, 255, 255, 0.2)"
                  align="stretch"
                >
                  <HStack justifyContent="space-between">
                    <Text fontSize="md" fontWeight="bold" color="cyan.300">
                      QUESTION {currentQuestionIndex + 1} / {questions.length}
                    </Text>
                    <Zap size={20} color="#99f6e4" />
                  </HStack>
                  <Text fontSize={{ base: 'lg', md: 'xl' }} color="white" pt={2}>
                    {currentQuestion}
                  </Text>
                </VStack>
              </MotionBox>

              {/* Answer Form */}
              <Box as="form" onSubmit={handleEvaluateAnswer}>
                <VStack spacing={4} align="stretch">
                  <Textarea
                    value={currentAnswer}
                    onChange={(e) => setCurrentAnswer(e.target.value)}
                    rows={6}
                    placeholder="Construct your detailed answer here..."
                    bg="rgba(10, 20, 50, 0.5)"
                    color="white"
                    borderColor="rgba(255, 255, 255, 0.2)"
                    borderRadius="lg"
                    _hover={{ borderColor: 'cyan.400' }}
                    _focus={{ borderColor: 'cyan.300', boxShadow: '0 0 15px rgba(0,255,255,0.3)', bg: "rgba(10, 20, 50, 0.8)" }}
                    required
                    isDisabled={isEvaluating || evaluation !== null}
                    transition="all 0.2s ease"
                  />
                  <HStack justifyContent="flex-end" spacing={4}>
                    {!evaluation && (
                       <Button
                        type="submit"
                        bgGradient="linear(to-r, cyan.500, blue.500)"
                        color="white"
                        isLoading={isEvaluating}
                        loadingText="Evaluating"
                        isDisabled={isEvaluating}
                        leftIcon={<Zap size={18} />}
                        _hover={{
                          bgGradient: "linear(to-r, cyan.400, blue.400)",
                          boxShadow: "0 0 25px rgba(0,255,255,0.4)",
                        }}
                      >
                        Submit & Evaluate
                      </Button>
                    )}
                    {evaluation && (
                      <Button
                        onClick={handleNextQuestion}
                        colorScheme="gray"
                        variant="outline"
                        isDisabled={isLastQuestion}
                        rightIcon={<RefreshCw size={16} />}
                        borderColor="rgba(255,255,255,0.4)"
                        _hover={{ bg: "rgba(255,255,255,0.1)" }}
                      >
                        Next Question
                      </Button>
                    )}
                  </HStack>
                </VStack>
              </Box>

              {/* Evaluation Result */}
              {evaluation && (
                <MotionBox
                  key={`eval-${currentQuestionIndex}`}
                  variants={contentVariants}
                  initial="hidden"
                  animate="visible"
                  p={6}
                  bg="rgba(79, 70, 229, 0.1)"
                  borderRadius="xl"
                  border="1px solid"
                  borderColor="rgba(129, 140, 248, 0.3)"
                >
                  <Heading size="md" color="indigo.300" mb={4}>Evaluation Feedback</Heading>
                  <Text fontSize="lg" fontWeight="bold" color="white" mb={2}>Score: {evaluation.score}</Text>
                  <Text color="gray.200" whiteSpace="pre-wrap" lineHeight="1.7">
                    {evaluation.feedback}
                  </Text>
                </MotionBox>
              )}
            </VStack>
          )}
        </MotionBox>
      </Container>
    </Flex>
  );
};

export default AIVivaSimulation;