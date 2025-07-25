import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Navbar from '../navbar/Navbar';
import './recommendation.css';
import KeyboardBackspaceIcon from '@mui/icons-material/KeyboardBackspace';
import { useNavigate } from "react-router-dom";
import { updateQuestionAPIMethod } from "../../api/question";
import Loader from '../loader/Loader';
import { useSelector } from "react-redux";

const Recommendation = () => {
    const [recList, setRecList] = useState([]); // top 10 recommendation
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { questionId, age, description, brand, market_status, allergies } = useParams();
    const navigate = useNavigate();
    const authUserId = useSelector((state) => state.user.id);

    function convertToNewUrl(originalUrl) {
        const prefix = 'https://dsld.od.nih.gov/label/';
        const suffix = '.pdf';
        const id = originalUrl.substring(prefix.length);
        return `https://api.ods.od.nih.gov/dsld/s3/pdf/${id}${suffix}`;
    }

    useEffect(() => {
        if (!authUserId) {
            navigate("/login");
            return;
        }
        setLoading(true);
        setError(null);
        const payload = {
            age: age || 25,
            description: decodeURIComponent(description || "My eyes feel dry."),
            brand: decodeURIComponent(brand || ""),
            market_status: market_status === 'true' || market_status === true,
            allergies: decodeURIComponent(allergies || "")
        };

        fetch('http://localhost:3001/run-python', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
            .then(response => response.json())
            .then(data => {
                if (data && data.recommendations) {
                    setRecList(data.recommendations.slice(0, 10));
                } else if (data && data.error) {
                    setError(data.error);
                    setRecList([]);
                } else {
                    setRecList([]);
                }
            })
            .catch(err => {
                setRecList([]);
                setError("Error fetching recommendations. Please try again later.");
                console.error("Error fetching recommendations:", err);
            })
            .finally(() => setLoading(false));
    }, [age, description, brand, market_status, allergies, authUserId, navigate]);

    const handleUpdateQuestion = () => {
        const rec_list = {
            rec_list: recList
        };
        updateQuestionAPIMethod(questionId, rec_list)
            .then((response) => {
                if (response.ok) {
                    console.log("Recommendation record has been saved.");
                } else {
                    console.log("Error saving recommendation.");
                }
            })
            .catch((err) => {
                console.error("Error when saving recommendation:", err);
            })
    }

    return (
        <div className='recommendation'>
            <Navbar />
            <div className='to_mainpage' onClick={() => { handleUpdateQuestion(); navigate('/mainpage') }}>
                <KeyboardBackspaceIcon />
                <div>Save & Exit</div>
            </div>
            <div className='recommendation_outer'>
                {loading && (
                    <>
                        <h1 className='loading_title'>Collecting results...</h1>
                        <p className='loading_subtext'>(This may take up to 10 seconds)</p>
                        <Loader />
                    </>
                )}
                {error && !loading && (
                    <>
                        <h1 className='loading_title'>No recommendations found</h1>
                        <p className='loading_subtext'>{error}</p>
                    </>
                )}
                {!loading && !error && recList.length === 0 && (
                    <>
                        <h1 className='loading_title'>No recommendations found</h1>
                        <p className='loading_subtext'>Try changing your answers or be more specific.</p>
                    </>
                )}
                {!loading && recList.length !== 0 && (
                    <>
                        <h1>Recommendations ({recList.length})</h1>
                        <div className='recommendation_container'>
                            {recList.map((d, idx) => (
                                <div className='recommendation_inner' key={idx}>
                                    <div className='recommendation_object'>
                                        <embed src={convertToNewUrl(d[0])} type="application/pdf" width="100%" height="500px" />
                                    </div>
                                    <div className='recommendation_object_bottom'>
                                        <h3>{d[2]}</h3>
                                        <div className='recommendation_object_bottom_bottom'>
                                            <p className='maker'>By {d[3]}</p>
                                            <div className='hover_over'>
                                                Hover over me!
                                            </div>
                                            <div className='hidden_div'>
                                                {d[13]}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}

export default Recommendation;