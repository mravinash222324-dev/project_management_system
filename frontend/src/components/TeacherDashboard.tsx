import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Flex,
  Heading,
  VStack,
  Text,
  Badge,
  Spinner,
  useToast,
  Tabs,
  TabList,
  Tab,
  Container,
} from '@chakra-ui/react';
import { motion } from 'framer-motion';

const MotionBox = motion(Box);

interface Submission {
  id: number;
  title: string;
  group_name: string;
  student: { username: string };
  relevance_score: number;
  feasibility_score: number;
  innovation_score: number;
  abstract_text: string;
}

const TeacherDashboard: React.FC = () => {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tabIndex, setTabIndex] = useState(0);
  const navigate = useNavigate();
  const toast = useToast();

  const viewType = tabIndex === 0 ? 'appointed' : 'unappointed';
  const endpoint =
    viewType === 'appointed'
      ? 'http://127.0.0.1:8000/teacher/appointed/'
      : 'http://127.0.0.1:8000/teacher/unappointed/';

  useEffect(() => {
    const fetchSubmissions = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('accessToken');
        if (!token) {
          navigate('/');
          return;
        }
        const response = await axios.get(endpoint, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSubmissions(response.data);
      } catch (err) {
        setError('Failed to fetch submissions. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchSubmissions();
  }, [viewType, navigate, endpoint]);

  const handleReview = async (submissionId: number, status: 'Approved' | 'Rejected') => {
    try {
      const token = localStorage.getItem('accessToken');
      await axios.patch(
        `http://127.0.0.1:8000/teacher/submissions/${submissionId}/`,
        { status },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast({
        title: 'Success',
        description: `Project status updated.`,
        status: 'success',
        duration: 4000,
        isClosable: true,
        position: 'top',
      });
      setSubmissions((prev) => prev.filter((sub) => sub.id !== submissionId));
    } catch (err) {
      toast({
        title: 'Update Failed',
        description: 'This project may have already been reviewed.',
        status: 'error',
        duration: 4000,
        isClosable: true,
        position: 'top',
      });
      console.error(err);
    }
  };

  const scoreColor = (score: number) => {
    if (score >= 7.5) return 'cyan';
    if (score >= 5) return 'yellow';
    return 'red';
  };

  if (loading) {
    return (
      <Flex minH="100vh" align="center" justify="center" bgGradient="linear(to-bl, #060B26, #0A042A)" color="white">
        <Spinner size="xl" color="cyan.400" thickness="4px" />
        <Text ml={4} fontSize="xl">Loading Submissions...</Text>
      </Flex>
    );
  }

  return (
    <Flex
      w="100%"
      minH="100vh"
      overflowY="auto"
      position="relative"
      justify="center"
      bgGradient="linear(to-bl, #060B26, #0A042A)"
      color="white"
      // --- THIS IS THE FIX TO HIDE THE SCROLLBAR ---
      sx={{
        '&::-webkit-scrollbar': {
          display: 'none',
        },
        'scrollbarWidth': 'none',
        '-ms-overflow-style': 'none',
      }}
    >
      <MotionBox position="absolute" top="-10%" left="-5%" w="72" h="72" rounded="full" bgGradient="radial(cyan.500, transparent)" filter="blur(150px)" opacity={0.3} animate={{ scale: [1, 1.2, 1] }} transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }} />
      <MotionBox position="absolute" bottom="-10%" right="-5%" w="80" h="80" rounded="full" bgGradient="radial(blue.500, transparent)" filter="blur(160px)" opacity={0.3} animate={{ scale: [1, 1.3, 1] }} transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }} />
      <Container maxW="container.lg" zIndex={2} py={{ base: 8, md: 16 }}>
        <motion.div initial={{ opacity: 0, y: -40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
          <Heading as="h1" size="2xl" mb={8} textAlign="center" bgGradient="linear(to-r, cyan.400, blue.400)" bgClip="text" fontWeight="extrabold">
            Teacher Review Dashboard
          </Heading>
        </motion.div>
        <Tabs isFitted variant="unstyled" onChange={(index) => setTabIndex(index)} mb={8}>
          <TabList borderBottom="2px solid" borderColor="rgba(255,255,255,0.2)">
            <Tab fontSize="lg" fontWeight="semibold" color="gray.400" _selected={{ color: 'cyan.300', boxShadow: '0px 2px 0px 0px cyan' }} transition="all 0.2s ease-in-out">
              Appointed Groups
            </Tab>
            <Tab fontSize="lg" fontWeight="semibold" color="gray.400" _selected={{ color: 'cyan.300', boxShadow: '0px 2px 0px 0px cyan' }} transition="all 0.2s ease-in-out">
              Unappointed Projects
            </Tab>
          </TabList>
        </Tabs>
        {submissions.length === 0 && !error ? (
          <MotionBox textAlign="center" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
            <Text fontSize="xl" color="gray.300">
              {viewType === 'appointed' ? 'No projects awaiting your review.' : 'No other unappointed projects found.'}
            </Text>
          </MotionBox>
        ) : error ? (
          <MotionBox textAlign="center" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <Text fontSize="xl" color="red.400">{error}</Text>
          </MotionBox>
        ) : (
          <VStack spacing={6}>
            {submissions.map((submission: Submission, index: number) => (
              <MotionBox
                key={submission.id}
                p={6}
                w="full"
                bg="rgba(28, 38, 78, 0.5)"
                border="1px solid"
                borderColor="rgba(255, 255, 255, 0.15)"
                borderRadius="2xl"
                boxShadow="0 10px 30px rgba(0,0,0,0.2)"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                whileHover={{
                  scale: 1.02,
                  borderColor: 'rgba(0, 255, 255, 0.5)',
                }}
              >
                <Flex justify="space-between" align="center" mb={2}>
                  <Heading size="md" color="cyan.300">{submission.title}</Heading>
                  <Text fontSize="sm" color="gray.400">Group: {submission.group_name}</Text>
                </Flex>
                <Text fontSize="sm" color="gray.300" mb={4}>
                  Submitted by: {submission.student.username}
                </Text>
                <Flex mb={4} gap={3} wrap="wrap">
                  <Badge variant="solid" colorScheme={scoreColor(submission.relevance_score)}>
                    Relevance: {submission.relevance_score}
                  </Badge>
                  <Badge variant="solid" colorScheme={scoreColor(submission.feasibility_score)}>
                    Feasibility: {submission.feasibility_score}
                  </Badge>
                  <Badge variant="solid" colorScheme={scoreColor(submission.innovation_score)}>
                    Innovation: {submission.innovation_score}
                  </Badge>
                </Flex>
                <Text mb={5} color="gray.200" noOfLines={4}>
                  <strong>Abstract:</strong> {submission.abstract_text}
                </Text>
                {viewType === 'appointed' && (
                  <Flex gap={4}>
                    <Button onClick={() => handleReview(submission.id, 'Approved')} bgGradient="linear(to-r, green.500, green.400)" _hover={{ bgGradient: 'linear(to-r, green.400, green.300)', boxShadow: '0 0 15px rgba(0,255,0,0.4)' }} transition="all 0.3s ease">
                      Approve
                    </Button>
                    <Button onClick={() => handleReview(submission.id, 'Rejected')} bgGradient="linear(to-r, red.600, red.500)" _hover={{ bgGradient: 'linear(to-r, red.500, red.400)', boxShadow: '0 0 15px rgba(255,0,0,0.4)' }} transition="all 0.3s ease">
                      Reject
                    </Button>
                  </Flex>
                )}
              </MotionBox>
            ))}
          </VStack>
        )}
      </Container>
    </Flex>
  );
};

export default TeacherDashboard;