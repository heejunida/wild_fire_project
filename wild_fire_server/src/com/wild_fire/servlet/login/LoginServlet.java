package com.wild_fire.servlet.login;

import com.wild_fire.DAO.UserDAO;

import javax.servlet.http.*;
import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;

@WebServlet("/login")
public class LoginServlet extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        req.setCharacterEncoding("UTF-8");
        String id = req.getParameter("user_id");
        String pw = req.getParameter("user_pw");

        UserDAO dao = new UserDAO();
        boolean success = dao.login(id, pw);

        resp.setContentType("application/json; charset=UTF-8");
        if (success) {
            HttpSession session = req.getSession();
            session.setAttribute("user", id);
            resp.getWriter().write("{\"result\":\"success\"}");
        } else {
            resp.getWriter().write("{\"result\":\"fail\"}");
        }
    }
}
