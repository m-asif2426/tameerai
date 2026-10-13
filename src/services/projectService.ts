import { Project, ProjectDocument, CreateProjectPayload } from "@/types";
import { INITIAL_PROJECTS, WORKSPACE_DOCUMENTS } from "@/data";

/**
 * Project Service
 * Placeholder architecture ready for FastAPI endpoint connections.
 * When backend is live, replace mock returns with:
 * return apiClient.get<Project[]>('/projects');
 */
export const projectService = {
  async getProjects(): Promise<Project[]> {
    // Simulated API call latency
    return Promise.resolve([...INITIAL_PROJECTS]);
  },

  async getProjectById(id: string): Promise<Project | null> {
    const project = INITIAL_PROJECTS.find((p) => p.id === id) || null;
    return Promise.resolve(project);
  },

  async createProject(payload: CreateProjectPayload): Promise<Project> {
    const newProject: Project = {
      id: `PRJ-${String(INITIAL_PROJECTS.length + 1).padStart(3, "0")}`,
      name: payload.name,
      nameUrdu: payload.name,
      location: payload.location,
      city: payload.city,
      cityUrdu: payload.city === "Lahore" ? "لاہور" : payload.city === "Karachi" ? "کراچی" : "اسلام آباد",
      type: payload.type,
      typeUrdu: payload.type,
      budgetCrore: payload.budgetCrore,
      budgetRaw: payload.budgetCrore * 10000000,
      spentCrore: 0,
      status: "Planning",
      statusUrdu: "منصوبہ بندی (Planning)",
      risk: "Low",
      riskUrdu: "کم (Low)",
      complianceScore: 100,
      lastUpdate: "Just now",
      lastUpdateUrdu: "ابھی ابھی",
      floors: payload.floors || 1,
      areaSqft: payload.areaSqft || "N/A",
      engineer: "Aslam Bhai",
    };
    return Promise.resolve(newProject);
  },

  async getProjectDocuments(projectId: string): Promise<ProjectDocument[]> {
    return Promise.resolve([...WORKSPACE_DOCUMENTS]);
  },
};
