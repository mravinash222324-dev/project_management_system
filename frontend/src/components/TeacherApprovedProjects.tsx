import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Heading,
  Text,
  VStack,
  Spinner,
  Alert,
  AlertIcon,
  Progress,
  Container,
  Badge,
  Flex,
  Center,
  HStack,
} from '@chakra-ui/react';
import { motion } from 'framer-motion';
import { BookCopy, User } from 'lucide-react';

// --- Interfaces & Animation Variants ---
interface ApprovedProject {
  id: number;
  submission_id: number;
  title: string;
  student_name: string;
  status: 'In Progress' | 'Completed' | 'Archived';
  progress_percentage: number;
  category: string;
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
const TeacherApprovedProjects: React.FC = () => {
  const [projects, setProjects] = useState<ApprovedProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const token = localStorage.getItem('accessToken');
        if (!token) {
          navigate('/');
          return;
        }
        const response = await axios.get('http://127.0.0.1:8000/teacher/approved-projects/', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setProjects(response.data);
      } catch (err) {
        setError('Failed to fetch approved projects.');
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, [navigate]);

  const getStatusBadge = (status: ApprovedProject['status']) => {
    switch (status) {
      case 'In Progress': return { colorScheme: 'yellow', text: 'In Progress' };
      case 'Completed': return { colorScheme: 'green', text: 'Completed' };
      case 'Archived': return { colorScheme: 'gray', text: 'Archived' };
      default: return { colorScheme: 'cyan', text: 'Approved' };
    }
  };

  if (loading) {
    return (
      <Center h="calc(100vh - 72px)" color="white">
        <Spinner size="xl" color="cyan.400" thickness="4px" />
        <Text ml={4} fontSize="xl">Loading Approved Projects...</Text>
      </Center>
    );
  }

  return (
    <Flex w="100%" h="calc(100vh - 72px)" justify="center" position="relative" color="white">
      <MotionBox position="absolute" top="0" left="0" w="80" h="80" rounded="full" bgGradient="radial(cyan.800, transparent)" filter="blur(200px)" opacity={0.2} zIndex={-1} />
      <MotionBox position="absolute" bottom="0" right="0" w="96" h="96" rounded="full" bgGradient="radial(blue.800, transparent)" filter="blur(200px)" opacity={0.2} zIndex={-1} />

      <Container maxW="container.xl" h="100%" overflowY="auto" py={{ base: 6, md: 8 }}
        sx={{
            '&::-webkit-scrollbar': { width: '4px' },
            '&::-webkit-scrollbar-track': { background: 'transparent' },
            '&::-webkit-scrollbar-thumb': { bg: 'rgba(255,255,255,0.2)', borderRadius: '24px' },
        }}>
        <VStack spacing={8}>
          <motion.div initial={{ opacity: 0, y: -40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
            <Heading as="h1" size="2xl" bgGradient="linear(to-r, cyan.400, blue.400)" bgClip="text" fontWeight="extrabold">
              Approved Projects Monitor
            </Heading>
          </motion.div>

          {error && (
            <Alert status="error" borderRadius="lg" bg="rgba(255,0,0,0.1)" border="1px solid rgba(255,0,0,0.3)">
              <AlertIcon color="red.300" />{error}
            </Alert>
          )}

          {projects.length === 0 && !error ? (
            <Center h="50vh">
              <Text fontSize="xl" color="gray.400">No projects are currently in an active state.</Text>
            </Center>
          ) : (
            <MotionVStack w="full" spacing={6} variants={containerVariants} initial="hidden" animate="visible">
              {projects.map((project) => {
                const status = getStatusBadge(project.status);
                return (
                  <MotionBox
                    key={project.id}
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
                    <VStack align="stretch" spacing={4}>
                      <Flex justify="space-between" align="center" direction={{ base: 'column', md: 'row' }} gap={3}>
                        <Heading size="md" color="cyan.300" textAlign={{ base: 'center', md: 'left' }}>{project.title}</Heading>
                        <Badge colorScheme={status.colorScheme} variant="solid" fontSize="sm">{status.text}</Badge>
                      </Flex>

                      <HStack spacing={6} color="gray.300" divider={<Text mx={2}>|</Text>}>
                         <HStack>
                            <User size={16} />
                            <Text>Student: <strong>{project.student_name}</strong></Text>
                         </HStack>
                         <HStack>
                            <BookCopy size={16} />
                            <Text>Category: <strong>{project.category}</strong></Text>
                         </HStack>
                      </HStack>
                      
                      <VStack align="stretch" spacing={2} pt={2}>
                        <HStack justify="space-between">
                            <Text fontSize="sm" fontWeight="bold" color="gray.200">Progress</Text>
                            <Text fontWeight="bold" color="cyan.300">{project.progress_percentage}%</Text>
                        </HStack>
                        <Progress value={project.progress_percentage} size="sm" colorScheme="cyan" borderRadius="full" bg="rgba(255,255,255,0.1)" />
                      </VStack>

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

export default TeacherApprovedProjects;