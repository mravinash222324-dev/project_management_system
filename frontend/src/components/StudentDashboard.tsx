import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  Spinner,
  Alert,
  AlertIcon,
  Input,
  useToast,
  Progress,
  FormControl,
  Flex,
  Container,
  Badge,
  Center,
} from '@chakra-ui/react';
import { motion } from 'framer-motion';
import { ArrowRight, Lock, Plus } from 'lucide-react';

// --- Interfaces & Animation Variants ---
interface Submission {
  id: number;
  title: string;
  status: 'Pending' | 'Approved' | 'Rejected' | 'In Progress';
  progress: number | null;
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } },
};

const MotionBox = motion(Box);
const MotionVStack = motion(VStack);

// --- Main Component ---
const StudentDashboard: React.FC = () => {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [progressInput, setProgressInput] = useState<{ [key: number]: number | '' }>({});
  const [isUpdating, setIsUpdating] = useState<number | null>(null);

  const navigate = useNavigate();
  const toast = useToast();

  useEffect(() => {
    const fetchSubmissions = async () => {
      try {
        const token = localStorage.getItem('accessToken');
        if (!token) {
          navigate('/');
          return;
        }

        const response = await axios.get('http://127.0.0.1:8000/student/submissions/', {
          headers: { Authorization: `Bearer ${token}` },
        });

        const subs: Submission[] = response.data;
        setSubmissions(subs);

        const initialProgress = subs.reduce((acc, sub) => {
          acc[sub.id] = sub.progress ?? '';
          return acc;
        }, {} as { [key: number]: number | '' });
        setProgressInput(initialProgress);
      } catch (err) {
        setError('Failed to fetch submissions.');
      } finally {
        setLoading(false);
      }
    };

    fetchSubmissions();
  }, [navigate]);

  const handleProgressUpdate = async (submissionId: number) => {
    const progressValue = progressInput[submissionId];
    if (
      progressValue === '' ||
      progressValue === undefined ||
      isNaN(Number(progressValue)) ||
      Number(progressValue) < 0 ||
      Number(progressValue) > 100
    ) {
      toast({
        title: 'Invalid Input',
        description: 'Please enter a number between 0 and 100.',
        status: 'warning',
        duration: 3000,
        isClosable: true,
        position: 'top',
      });
      return;
    }

    setIsUpdating(submissionId);
    try {
      const token = localStorage.getItem('accessToken');
      await axios.patch(
        `http://127.0.0.1:8000/projects/progress/update/${submissionId}/`,
        { progress: Number(progressValue) },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSubmissions((prev) =>
        prev.map((sub) =>
          sub.id === submissionId ? { ...sub, progress: Number(progressValue) } : sub
        )
      );
      toast({
        title: 'Progress Updated',
        status: 'success',
        duration: 3000,
        isClosable: true,
        position: 'top',
      });
    } catch (err) {
      toast({
        title: 'Update Failed',
        description: 'Could not update progress. The project may not be approved yet.',
        status: 'error',
        duration: 4000,
        isClosable: true,
        position: 'top',
      });
    } finally {
      setIsUpdating(null);
    }
  };

  const getStatusBadge = (status: Submission['status']) => {
    switch (status) {
      case 'Approved':
        return { colorScheme: 'cyan', text: 'Approved' };
      case 'In Progress':
        return { colorScheme: 'yellow', text: 'In Progress' };
      case 'Rejected':
        return { colorScheme: 'red', text: 'Rejected' };
      default:
        return { colorScheme: 'gray', text: 'Pending' };
    }
  };

  if (loading) {
    return (
      <Center h="calc(100vh - 72px)" color="white">
        <Spinner size="xl" color="cyan.400" thickness="4px" />
        <Text ml={4} fontSize="xl">
          Loading Dashboard...
        </Text>
      </Center>
    );
  }

  return (
    <Flex w="100%" h="calc(100vh - 72px)" justify="center" position="relative" color="white">
      <MotionBox
        position="absolute"
        top="0"
        left="0"
        w="80"
        h="80"
        rounded="full"
        bgGradient="radial(cyan.800, transparent)"
        filter="blur(200px)"
        opacity={0.2}
        zIndex={-1}
      />
      <MotionBox
        position="absolute"
        bottom="0"
        right="0"
        w="96"
        h="96"
        rounded="full"
        bgGradient="radial(blue.800, transparent)"
        filter="blur(200px)"
        opacity={0.2}
        zIndex={-1}
      />

      <Container
        maxW="container.xl"
        h="100%"
        overflowY="auto"
        py={{ base: 6, md: 8 }}
        sx={{
          '&::-webkit-scrollbar': { width: '4px' },
          '&::-webkit-scrollbar-track': { background: 'transparent' },
          '&::-webkit-scrollbar-thumb': { bg: 'rgba(255,255,255,0.2)', borderRadius: '24px' },
        }}
      >
        <VStack spacing={8}>
          <motion.div
            initial={{ opacity: 0, y: -40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <Heading
              as="h1"
              size="2xl"
              bgGradient="linear(to-r, cyan.400, blue.400)"
              bgClip="text"
              fontWeight="extrabold"
            >
              My Project Dashboard
            </Heading>
          </motion.div>

          <Button
            onClick={() => navigate('/submit')}
            bgGradient="linear(to-r, cyan.500, blue.500)"
            color="white"
            size="lg"
            leftIcon={<Plus size={20} />}
            _hover={{
              bgGradient: 'linear(to-r, cyan.400, blue.400)',
              boxShadow: '0 0 25px rgba(0,255,255,0.4)',
              transform: 'translateY(-2px)',
            }}
            transition="all 0.3s ease"
          >
            Submit New Project
          </Button>

          {error && (
            <Alert status="error" borderRadius="lg" bg="rgba(255,0,0,0.1)" border="1px solid rgba(255,0,0,0.3)">
              <AlertIcon color="red.300" />
              {error}
            </Alert>
          )}

          {submissions.length === 0 && !error ? (
            <Center h="40vh">
              <Text fontSize="xl" color="gray.400">
                You haven't submitted any projects yet.
              </Text>
            </Center>
          ) : (
            <MotionVStack w="full" spacing={6} variants={containerVariants} initial="hidden" animate="visible">
              {submissions.map((submission) => {
                const status = getStatusBadge(submission.status);
                const isActionable = submission.status === 'Approved' || submission.status === 'In Progress';

                return (
                  <MotionBox
                    key={submission.id}
                    variants={itemVariants}
                    w="full"
                    p={6}
                    bg="rgba(28, 38, 78, 0.5)"
                    border="1px solid rgba(255,255,255,0.15)"
                    borderRadius="2xl"
                    boxShadow="0 10px 30px rgba(0,0,0,0.2)"
                    whileHover={{ transform: 'translateY(-5px)', borderColor: 'rgba(0, 255, 255, 0.5)' }}
                    transition={{ duration: 0.2 }}
                  >
                    <VStack align="stretch" spacing={5}>
                      <Flex justify="space-between" align="center" direction={{ base: 'column', md: 'row' }} gap={4}>
                        <VStack align={{ base: 'center', md: 'flex-start' }}>
                          <Heading size="md" color="cyan.300">
                            {submission.title}
                          </Heading>
                          <Badge colorScheme={status.colorScheme} variant="solid">
                            {status.text}
                          </Badge>
                        </VStack>

                        {/* --- FIXED AI VIVA BUTTON --- */}
                        <Button
                          onClick={() => isActionable && navigate(`/ai-viva/${submission.id}`)}
                          isDisabled={!isActionable}
                          rightIcon={isActionable ? <ArrowRight size={16} /> : <Lock size={16} />}
                          bgGradient={isActionable ? 'linear(to-r, teal.500, blue.500)' : undefined}
                          bg={!isActionable ? 'rgba(255,255,255,0.05)' : undefined}
                          color={!isActionable ? 'gray.400' : 'white'}
                          cursor={!isActionable ? 'not-allowed' : 'pointer'}
                          _hover={
                            isActionable
                              ? {
                                  bgGradient: 'linear(to-r, teal.400, blue.400)',
                                  boxShadow: '0 0 15px rgba(0,255,255,0.3)',
                                }
                              : {}
                          }
                          _disabled={{
                            bg: 'rgba(255,255,255,0.05)',
                            color: 'gray.500',
                            cursor: 'not-allowed',
                            opacity: 0.7,
                            boxShadow: 'none',
                          }}
                        >
                          {isActionable ? 'AI Viva Simulation' : 'Viva Locked'}
                        </Button>
                      </Flex>

                      {isActionable && (
                        <VStack align="stretch" spacing={4} pt={4} borderTop="1px solid" borderColor="rgba(255,255,255,0.1)">
                          <HStack>
                            <Text fontSize="sm" fontWeight="bold" color="gray.200" minW="80px">
                              Progress:
                            </Text>
                            <Progress
                              value={submission.progress ?? 0}
                              size="sm"
                              colorScheme="cyan"
                              borderRadius="full"
                              flex="1"
                              bg="rgba(255,255,255,0.1)"
                            />
                            <Text fontWeight="bold" color="cyan.300">
                              {submission.progress ?? 0}%
                            </Text>
                          </HStack>
                          <HStack
                            as="form"
                            onSubmit={(e) => {
                              e.preventDefault();
                              handleProgressUpdate(submission.id);
                            }}
                          >
                            <FormControl>
                              <Input
                                type="number"
                                placeholder="e.g., 25"
                                value={progressInput[submission.id] ?? ''}
                                onChange={(e) =>
                                  setProgressInput({
                                    ...progressInput,
                                    [submission.id]: e.target.value === '' ? '' : parseInt(e.target.value),
                                  })
                                }
                                size="sm"
                                borderRadius="md"
                                bg="rgba(0,0,0,0.2)"
                                borderColor="rgba(255,255,255,0.2)"
                                _hover={{ borderColor: 'cyan.400' }}
                                _focus={{ borderColor: 'cyan.300', boxShadow: '0 0 10px rgba(0,255,255,0.3)' }}
                              />
                            </FormControl>
                            <Button type="submit" size="sm" colorScheme="green" isLoading={isUpdating === submission.id} loadingText="Saving">
                              Update
                            </Button>
                          </HStack>
                        </VStack>
                      )}
                    </VStack>
                  </MotionBox>
                );
              })}
            </MotionVStack>
          )}
        </VStack>
      </Container>
    </Flex>
  );
};

export default StudentDashboard;
