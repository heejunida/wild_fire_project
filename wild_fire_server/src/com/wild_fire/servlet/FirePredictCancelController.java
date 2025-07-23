package com.wild_fire.servlet;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import com.wild_fire.servlet.FirePredictController; // Add this import statement

@WebServlet("/fire-predict-cancel")
public class FirePredictCancelController extends HttpServlet {

    protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        String requestId = request.getParameter("requestId");
        if (requestId == null || requestId.isEmpty()) {
            response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            response.getWriter().write("{\"error\": \"Missing requestId parameter\"}");
            return;
        }

        // Directly access the static map from FirePredictController
        Process process = FirePredictController.activeProcesses.remove(requestId); // Remove and get the process
        if (process != null) {
            System.out.println("Attempting to terminate process for requestId: " + requestId);
            process.destroyForcibly(); // Forcefully terminate the process
            try {
                process.waitFor(); // Wait for the process to actually terminate
                System.out.println("Process for requestId " + requestId + " terminated.");
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                System.err.println("Interrupted while waiting for process termination: " + e.getMessage());
            }
            response.setStatus(HttpServletResponse.SC_OK);
            response.getWriter().write("{\"status\": \"cancelled\", \"requestId\": \"" + requestId + "\"}");
        } else {
            System.out.println("No active process found for requestId: " + requestId);
            response.setStatus(HttpServletResponse.SC_NOT_FOUND);
            response.getWriter().write("{\"error\": \"No active process found for requestId: " + requestId + "\"}");
        }
    }
}
